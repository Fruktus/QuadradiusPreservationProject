interface RufflePlayerConfig {
    config?: Record<string, unknown>;
    [key: string]: unknown;
}

interface Window {
    RufflePlayer?: RufflePlayerConfig;
}
