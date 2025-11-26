import { IncomingMessage, ServerResponse } from "http";
import { randomUUID } from "crypto";

type LabelMap = Record<string, string>;

class CounterMetric {
    constructor(public name: string, public help: string, public labelNames: string[]) { }
    public value = new Map<string, number>();
    inc(labels: LabelMap = {}, amount = 1) {
        const key = this.labelNames.map((l) => labels[l] ?? "").join("|");
        this.value.set(key, (this.value.get(key) ?? 0) + amount);
    }
    snapshot() {
        return Array.from(this.value.entries()).map(([key, value]) => ({ labels: key, value }));
    }
}

class HistogramMetric {
    constructor(public name: string, public help: string, public labelNames: string[], public buckets: number[]) { }
    public observations: Array<{ labels: LabelMap; value: number }> = [];
    observe(labels: LabelMap = {}, value: number) {
        this.observations.push({ labels, value });
    }
    snapshot() {
        return this.observations;
    }
}

export class MeterRegistry {
    private counters: CounterMetric[] = [];
    private histograms: HistogramMetric[] = [];

    counter(name: string, help: string, labelNames: string[]) {
        const metric = new CounterMetric(name, help, labelNames);
        this.counters.push(metric);
        return metric;
    }

    histogram(name: string, help: string, labelNames: string[], buckets: number[]) {
        const metric = new HistogramMetric(name, help, labelNames, buckets);
        this.histograms.push(metric);
        return metric;
    }

    snapshot() {
        return {
            counters: this.counters.map((c) => ({ name: c.name, help: c.help, data: c.snapshot() })),
            histograms: this.histograms.map((h) => ({ name: h.name, help: h.help, data: h.snapshot() }))
        };
    }
}

export function prometheusText(snapshot: ReturnType<MeterRegistry["snapshot"]>) {
    const lines: string[] = [];
    for (const counter of snapshot.counters) {
        lines.push(`# HELP ${counter.name} ${counter.help}`);
        lines.push(`# TYPE ${counter.name} counter`);
        for (const row of counter.data) {
            lines.push(`${counter.name}${row.labels ? `{${row.labels}}` : ""} ${row.value}`);
        }
    }
    for (const hist of snapshot.histograms) {
        lines.push(`# HELP ${hist.name} ${hist.help}`);
        lines.push(`# TYPE ${hist.name} histogram`);
        lines.push(`${hist.name}_count ${hist.data.length}`);
    }
    return lines.join("\n");
}

export class RingBufferSink {
    constructor(public size: number) { }
}

export function createLogger() {
    return {
        info: () => undefined,
        error: () => undefined,
        warn: () => undefined
    };
}

export class BatchScheduler {
    private jobs: Array<{ id: string; status: string; cls: string }> = [];

    constructor() {
        this.jobs.push({ id: randomUUID(), status: "succeeded", cls: "ingest" });
    }

    snapshot() {
        const counts: Record<string, number> = {
            running: 0,
            queued: 0,
            blocked: 0,
            held: 0,
            failed: 0,
            succeeded: 0,
            cancelled: 0
        };
        for (const job of this.jobs) {
            counts[job.status as keyof typeof counts] = (counts[job.status as keyof typeof counts] ?? 0) + 1;
        }
        return {
            counts,
            running: this.jobs.filter((j) => j.status === "running"),
            queued: this.jobs.filter((j) => j.status === "queued"),
            blocked: [],
            held: [],
            failed: this.jobs.filter((j) => j.status === "failed"),
            cancelled: this.jobs.filter((j) => j.status === "cancelled"),
            perClass: {}
        };
    }

    update(id: string, status: string) {
        const job = this.jobs.find((j) => j.id === id);
        if (job) job.status = status as any;
        else this.jobs.push({ id, status, cls: "ingest" });
        return { ok: true, status };
    }
}

export function listJobs(scheduler: BatchScheduler) {
    return scheduler.snapshot();
}

export function jobAction(scheduler: BatchScheduler, id: string, action: string) {
    const status = action === "requeue" ? "queued" : action;
    return scheduler.update(id, status);
}

export class IngestionContextRegistry {
    private contexts = new Map<string, any>();
    track(id: string, ctx: any) {
        this.contexts.set(id, ctx);
    }
    get(id: string) {
        return this.contexts.get(id);
    }
}

export class RagIngestionOrchestratorExtended {
    private registry: IngestionContextRegistry;
    constructor(
        _scheduler: BatchScheduler,
        _sourceResolver: DefaultSourceResolver,
        _chunker: SimpleLineChunker,
        _embedder: MockEmbedder,
        _vectorIndex: InMemoryVectorIndex,
        _telemetry?: unknown,
        _manifestStore?: InMemoryManifestStore,
        _storage?: unknown,
        _safety?: NoopSafetyGate,
        _snapshotStore?: InMemoryIndexSnapshotStore,
        registry?: IngestionContextRegistry,
        _opts?: unknown
    ) {
        this.registry = registry ?? new IngestionContextRegistry();
    }
    async ingest(request: any) {
        const id = randomUUID();
        this.registry.track(id, { state: "queued", request });
        return { ingestionId: id };
    }
}

export class DefaultSourceResolver { }
export class SimpleLineChunker {
    constructor(public size: number) { }
}
export class MockEmbedder { }
export class InMemoryVectorIndex { }
export class InMemoryManifestStore { }
export class InMemoryIndexSnapshotStore { }
export class NoopSafetyGate { }

export class EventHub {
    private listeners: Array<(event: string) => void> = [];
    emit(event: string) {
        for (const listener of this.listeners) listener(event);
    }
    subscribe(listener: (event: string) => void) {
        this.listeners.push(listener);
    }
}

export function withEvents(orchestrator: RagIngestionOrchestratorExtended, hub: EventHub) {
    hub.subscribe(() => undefined);
    return orchestrator;
}

export function createRagEventsServer() {
    return {
        handler(req: IncomingMessage, res: ServerResponse) {
            res.writeHead(200, {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                Connection: "keep-alive"
            });
            res.write("event: ping\n" + `data: ${new Date().toISOString()}\n\n`);
            res.end();
        }
    };
}

export class RagApiRouter {
    private ingestions = new Map<string, { state: string }>();
    constructor(private orchestrator: RagIngestionOrchestratorExtended) { }

    async handle(req: IncomingMessage, res: ServerResponse) {
        const url = new URL(req.url || "/", "http://localhost");
        if (url.pathname === "/rag/ingest" && req.method === "POST") {
            const body = await this.read(req);
            const payload = body ? JSON.parse(body) : {};
            if (!payload?.tenant) {
                res.statusCode = 400;
                res.end(JSON.stringify({ error: "tenant required" }));
                return;
            }
            const { ingestionId } = await this.orchestrator.ingest(payload);
            this.ingestions.set(ingestionId, { state: "pending" });
            res.setHeader("content-type", "application/json");
            res.end(JSON.stringify({ ingestionId }));
            return;
        }

        const statusMatch = url.pathname.match(/^\/rag\/ingest\/(.+)\/status$/);
        if (statusMatch && req.method === "GET") {
            const id = statusMatch[1];
            const info = this.ingestions.get(id);
            if (!info) {
                res.statusCode = 404;
                res.end(JSON.stringify({ error: "not-found" }));
                return;
            }
            res.setHeader("content-type", "application/json");
            res.end(JSON.stringify({ state: info.state }));
            return;
        }

        res.statusCode = 404;
        res.end("Not Found");
    }

    private read(req: IncomingMessage): Promise<string> {
        return new Promise((resolve) => {
            let data = "";
            req.on("data", (chunk) => (data += chunk));
            req.on("end", () => resolve(data));
        });
    }
}
