FROM node:24-bookworm-slim AS build

WORKDIR /workspace
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml tsconfig.base.json ./
COPY gateway/package.json gateway/package.json
COPY ui/package.json ui/package.json
COPY e2e/package.json e2e/package.json
RUN npm install --global "$(node -p 'require("./package.json").packageManager')" && \
    pnpm install --frozen-lockfile
COPY gateway/ gateway/
RUN pnpm --filter @gridbot/gateway build

FROM node:24-bookworm-slim

WORKDIR /app
COPY --from=build /workspace/gateway/package.json ./
COPY --from=build /workspace/gateway/dist ./dist
USER node
CMD ["node", "dist/main.js"]
