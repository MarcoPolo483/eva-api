import { vi } from "vitest";
import * as stub from "../test-stubs/eva-core";

// Mock the monorepo package 'eva-core' to our local stub for all tests
vi.mock("eva-core", () => stub);
