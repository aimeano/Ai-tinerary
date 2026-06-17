// src/vite-env.d.ts
/// <reference types="vite/client" />  
/// <reference types="react" />  
/// <reference types="react-dom" />  

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: "http://127.0.0.1:8000"
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
