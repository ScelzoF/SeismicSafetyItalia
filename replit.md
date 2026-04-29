# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies.
Also includes a Python/Streamlit seismic monitoring app (SismoCampania).

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)
- **Python**: 3.11 (Streamlit seismic app)

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally

## Artifacts

### SismoCampania (artifacts/sismo-campania)
- **Type**: Python/Streamlit web app
- **Port**: 5000
- **Preview Path**: /
- **Source**: Replicated from https://github.com/ScelzoF/SeismicSafetyItalia
- **Modules**: data_service, visualization, emergenza, weather, forum, utils, ai_analysis, ai_chat, orario, translations_lib, ml_forecast_service, ingv_monitor, supabase_utils, chat_pubblica, security
- **Features**: Real-time seismic monitoring (INGV/USGS), maps (Folium), weather (Open-Meteo), ML forecasting, AI chat, emergency routes, community forum
- **Data Sources**: INGV, USGS, Open-Meteo, OpenAQ
- **Optional**: Supabase (for forum/chat persistence) - set SUPABASE_URL and SUPABASE_KEY env vars
- **Run**: `cd artifacts/sismo-campania && streamlit run app.py --server.port 5000`

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.
