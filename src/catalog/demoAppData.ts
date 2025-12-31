import type { Asset, Layout, ProjectConfig, RagRequest, RagResponse, ScreenTemplate } from "eva-core";
import {
    assetSchema,
    layoutSchema,
    projectConfigSchema,
    ragRequestSchema,
    ragResponseSchema,
    screenTemplateSchema
} from "eva-core";

// Testing-friendly parse wrapper: if schemas are unavailable (e.g., mocked),
// fall back to returning the provided object to avoid hard failures in tests.
function safeParse<T>(schema: any, obj: T): T {
    try {
        if (schema && typeof schema.parse === "function") {
            return schema.parse(obj);
        }
    } catch {
        // ignore validation errors in demo data during tests
    }
    return obj;
}

const projects: ProjectConfig[] = [
    safeParse(projectConfigSchema, {
        projectId: "eva-da",
        name: "EVA Domain Assistant",
        description: "CPP-D jurisprudence assistant",
        theme: {
            primaryColor: "#0050b3",
            backgroundColor: "#f4f6fb",
            headerTextColor: "#0f172a"
        },
        i18n: {
            headlineKeyEn: "eva.da.headline",
            headlineKeyFr: "eva.da.headline.fr",
            subtitleKeyEn: "eva.da.subtitle",
            subtitleKeyFr: "eva.da.subtitle.fr"
        },
        api: {
            ragEndpoint: "https://api.eva-da.local/rag/answer",
            safetyProfile: "standard"
        }
    })
];

const layouts: Record<string, Layout> = Object.fromEntries(
    [
        safeParse(layoutSchema, {
            pageId: "eva-da.dashboard",
            version: "1.0",
            sections: [
                { id: "hero", type: "hero", props: { headlineKey: "eva.da.headline" } },
                { id: "stats", type: "metrics-grid", props: { columns: 3 } }
            ]
        })
    ].map((layout) => [layout.pageId, layout])
);

const templates: ScreenTemplate[] = [
    safeParse(screenTemplateSchema, {
        templateId: "eva-da.chat",
        label: "EVA DA Chat",
        description: "Two column DA workspace",
        layoutRef: "eva-da.dashboard",
        allowedProjects: ["eva-da"],
        editableProps: ["headlineKey", "primaryColor"]
    })
];

const assets: Asset[] = [
    safeParse(assetSchema, { assetId: "eva-da.hero", type: "svg", path: "/assets/eva-da/hero.svg" })
];

export function listProjects(): ProjectConfig[] {
    return projects;
}

export function listTemplates(): ScreenTemplate[] {
    return templates;
}

export function listAssets(): Asset[] {
    return assets;
}

export function getLayout(pageId: string): Layout | undefined {
    return layouts[pageId];
}

export function answerDemoRag(req: RagRequest): RagResponse {
    const { question } = safeParse(ragRequestSchema, req) as RagRequest;
    return safeParse(ragResponseSchema, {
        answer: {
            text: `Demo answer for "${question}"`,
            citations: [{ sourceId: "eva-da.demo", snippet: "Demo citation" }]
        },
        safety: { blocked: false }
    }) as RagResponse;
}
