"use client";
import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

export type Theme = "light" | "dark";
const KEY = "delta-theme";

/** Runs before paint (inlined in <head>) so the first frame already has the right theme. */
export const THEME_BOOT = `(function(){try{var t=localStorage.getItem('${KEY}');if(t!=='light'&&t!=='dark'){t=matchMedia('(prefers-color-scheme: light)').matches?'light':'dark'}document.documentElement.dataset.theme=t}catch(e){document.documentElement.dataset.theme='dark'}})();`;

export function currentTheme(): Theme {
  if (typeof document === "undefined") return "dark";
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

/** Light / dark switch; charts listen for the `delta:theme` event to recolor. */
export function ThemeToggle({ variant = "icon" }: { variant?: "icon" | "segmented" }) {
  const [theme, setTheme] = useState<Theme>("dark");
  useEffect(() => setTheme(currentTheme()), []);
  const apply = (next: Theme) => {
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem(KEY, next);
    } catch {
      /* private mode: theme still applies for this visit */
    }
    setTheme(next);
    window.dispatchEvent(new Event("delta:theme"));
  };
  if (variant === "segmented")
    return (
      <div className="theme-switch" role="group" aria-label="Giao diện">
        {(["light", "dark"] as Theme[]).map((t) => (
          <button key={t} type="button" aria-pressed={theme === t} onClick={() => apply(t)}>
            {t === "light" ? <Sun size={14} /> : <Moon size={14} />}
            {t === "light" ? "Sáng" : "Tối"}
          </button>
        ))}
      </div>
    );
  return (
    <button
      type="button"
      className="icon-button theme-icon"
      aria-label={theme === "dark" ? "Chuyển sang giao diện sáng" : "Chuyển sang giao diện tối"}
      title={theme === "dark" ? "Giao diện sáng" : "Giao diện tối"}
      onClick={() => apply(theme === "dark" ? "light" : "dark")}
    >
      {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
    </button>
  );
}
