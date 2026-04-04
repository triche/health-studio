import { useState, useCallback, type ReactNode } from "react";
import { ToastContext } from "./ToastContext";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: ToastType = "info") => {
    const id = nextId++;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const colorMap: Record<ToastType, string> = {
    success: "bg-green-600 text-white",
    error: "bg-red-600 text-white",
    info: "bg-primary text-white",
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="alert"
            className={`rounded-lg px-4 py-2.5 text-sm font-medium shadow-lg ${colorMap[toast.type]}`}
          >
            <div className="flex items-center gap-2">
              <span>{toast.message}</span>
              <button
                onClick={() => dismiss(toast.id)}
                className="ml-2 opacity-70 hover:opacity-100"
                aria-label="Dismiss"
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
