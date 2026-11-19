FROM node:24-bookworm-slim AS build

WORKDIR /workspace
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml tsconfig.base.json ./
COPY gateway/package.json gateway/package.json
COPY ui/package.json ui/package.json
COPY e2e/package.json e2e/package.json
RUN npm install --global "$(node -p 'require("./package.json").packageManager')" && \
    pnpm install --frozen-lockfile
COPY gateway/ gateway/
COPY ui/ ui/
RUN pnpm --filter @gridbot/ui build && \
    pnpm --filter @gridbot/gateway build && \
    pnpm --filter @gridbot/gateway deploy --prod --legacy /out

FROM node:24-bookworm-slim

WORKDIR /app
COPY --from=build /out/package.json ./
COPY --from=build /out/node_modules ./node_modules
COPY --from=build /workspace/gateway/dist ./dist
COPY --from=build /workspace/ui/dist ./ui
# Listen on every container interface; Compose decides what the host sees.
ENV GRIDBOT_HOST=0.0.0.0 \
    GRIDBOT_UI_DIR=/app/ui
EXPOSE 8080
USER node
CMD ["node", "dist/main.js"]
