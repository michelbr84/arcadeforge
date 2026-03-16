/**
 * @arcadeforge/shared
 *
 * Shared types, constants, and schemas used across the ArcadeForge monorepo.
 */

export const APP_NAME = "ArcadeForge";

export type GameVisibility = "private" | "public" | "unlisted";

export type GameGenre = string;

export type ValidationStatus = "pending" | "running" | "passed" | "failed";

export type PlaySessionStatus = "starting" | "running" | "stopped" | "expired";
