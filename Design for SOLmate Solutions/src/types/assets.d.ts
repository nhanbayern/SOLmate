/// <reference types="vite/client" />

declare module "*.csv?raw" {
  const content: string;
  export default content;
}

declare module "@mockdata/*?raw" {
  const content: string;
  export default content;
}
