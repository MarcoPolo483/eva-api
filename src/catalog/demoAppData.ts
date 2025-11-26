import type { Asset, Layout, ProjectConfig, RagRequest, RagResponse, ScreenTemplate } from "eva-core";
import {
    assetSchema,
    layoutSchema,
    projectConfigSchema,
    ragRequestSchema,
    ragResponseSchema,
    screenTemplateSchema
} from "eva-core";

const projects: ProjectConfig[] = [
    projectConfigSchema.parse({
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
        layoutSchema.parse({
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
    screenTemplateSchema.parse({
        templateId: "eva-da.chat",
        label: "EVA DA Chat",
        description: "Two column DA workspace",
        layoutRef: "eva-da.dashboard",
        allowedProjects: ["eva-da"],
        editableProps: ["headlineKey", "primaryColor"]
    })
];

const assets: Asset[] = [
    assetSchema.parse({ assetId: "eva-da.hero", type: "svg", path: "/assets/eva-da/hero.svg" })
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
    const { question } = ragRequestSchema.parse(req);
    return ragResponseSchema.parse({
        answer: {
            text: `Demo answer for "${question}"`,
            citations: [{ sourceId: "eva-da.demo", snippet: "Demo citation" }]
        },
        safety: { blocked: false }
    });
}
