/**
 * Ocean Intelligence API Service
 *
 * Reserved for Prototype 1 Phase 2.
 *
 * Future responsibilities:
 * - FastAPI communication
 * - geographic bounding-box queries
 * - temperature-data retrieval
 * - depth/time filtering
 * - normalized API responses
 *
 * No backend requests are required during Frontend Phase 1.
 */

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
