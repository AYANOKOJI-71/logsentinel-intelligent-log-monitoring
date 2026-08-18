/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly LOGWATCH_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
