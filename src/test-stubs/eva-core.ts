// Test-only stub for eva-core exports used by eva-api tests
// Provides minimal types and Zod schemas so demoAppData can validate sample data
import { z } from "zod";
// Test visibility: indicate stub module is loaded during tests
console.log("eva-core stub loaded");

export const assetSchema = z.object({
  assetId: z.string(),
  type: z.string(),
  path: z.string(),
});
export type Asset = z.infer<typeof assetSchema>;

const sectionSchema = z.object({
  id: z.string(),
  type: z.string(),
  props: z.any().optional(),
});
export const layoutSchema = z.object({
  pageId: z.string(),
  version: z.string(),
  sections: z.array(sectionSchema),
});
export type Layout = z.infer<typeof layoutSchema>;  projectId: z.string(),
  name: z.string(),
  description: z.string(),
  theme: z
    .object({
      primaryColor: z.string().optional(),
      backgroundColor: z.string().optional(),
      headerTextColor: z.string().optional(),
    })
    .optional(),
  i18n: z
    .object({
      headlineKeyEn: z.string().optional(),
      headlineKeyFr: z.string().optional(),
      subtitleKeyEn: z.string().optional(),
      subtitleKeyFr: z.string().optional(),
    })
    .optional(),
  api: z
    .object({
      ragEndpoint: z.string().url().optional(),
      safetyProfile: z.string().optional(),
    })
    .optional(),
});
export type ProjectConfig = z.infer<typeof projectConfigSchema>;

export const screenTemplateSchema = z.object({
  templateId: z.string(),
  label: z.string(),
  description: z.string(),
  layoutRef: z.string(),
  allowedProjects: z.array(z.string()),
  editableProps: z.array(z.string()).optional(),
});
export type ScreenTemplate = z.infer<typeof screenTemplateSchema>;

export const ragRequestSchema = z.object({
  question: z.string(),
});
export type RagRequest = z.infer<typeof ragRequestSchema>;

export const ragResponseSchema = z.object({
  answer: z.object({
    text: z.string(),
    citations: z.array(
      z.object({ sourceId: z.string(), snippet: z.string().optional() })
    ),
  }),
  safety: z.object({ blocked: z.boolean() }),
});
export type RagResponse = z.infer<typeof ragResponseSchema>;
