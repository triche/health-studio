import "@testing-library/jest-dom";

// Stub URL.createObjectURL for Plotly.js in jsdom
if (typeof window !== "undefined" && !window.URL.createObjectURL) {
  window.URL.createObjectURL = () => "";
  window.URL.revokeObjectURL = () => {};
}
