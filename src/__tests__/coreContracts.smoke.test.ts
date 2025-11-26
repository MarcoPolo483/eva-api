import { describe, expect, it } from "vitest";

import { answerDemoRag, getLayout, listProjects, listTemplates } from "../catalog/demoAppData.js";

describe("eva-core contracts wiring", () => {
    it("provides typed demo catalog data", () => {
        const [project] = listProjects();
        expect(project.projectId).toBe("eva-da");
        const template = listTemplates()[0];
        expect(template.layoutRef).toBe("eva-da.dashboard");
        expect(getLayout("eva-da.dashboard")).toBeDefined();
    });

    it("answers demo rag requests via schema validation", () => {
        const resp = answerDemoRag({ question: "What is CPP-D?", projectId: "eva-da" });
        expect(resp.answer.text).toContain("CPP-D");
    });
});
