import "@testing-library/jest-dom";

// Stub URL.createObjectURL for Plotly.js in jsdom
if (typeof window !== "undefined" && !window.URL.createObjectURL) {
  window.URL.createObjectURL = () => "";
  window.URL.revokeObjectURL = () => {};
}

// Ensure localStorage is available in jsdom
if (typeof window !== "undefined" && !window.localStorage?.getItem) {
  const store: Record<string, string> = {};
  Object.defineProperty(window, "localStorage", {
    value: {
      getItem: (key: string) => store[key] ?? null,
      setItem: (key: string, value: string) => {
        store[key] = value;
      },
      removeItem: (key: string) => {
        delete store[key];
      },
      clear: () => {
        for (const key of Object.keys(store)) delete store[key];
      },
      get length() {
        return Object.keys(store).length;
      },
      key: (index: number) => Object.keys(store)[index] ?? null,
    },
    writable: true,
  });
}
