"use client";
export function WorkspaceTabs({
  tabs,
  value,
  onChange,
  scope,
}: {
  tabs: readonly (readonly [string, string])[];
  value: string;
  onChange: (value: string) => void;
  scope: string;
}) {
  return (
    <div
      className="tabs-line workspace-tabs"
      role="tablist"
      aria-label="Nội dung workspace"
    >
      {tabs.map(([id, label], index) => (
        <button
          key={id}
          id={`${scope}-${id}`}
          role="tab"
          aria-selected={value === id}
          aria-controls={`${scope}-panel`}
          tabIndex={value === id ? 0 : -1}
          className={value === id ? "active" : ""}
          onClick={() => onChange(id)}
          onKeyDown={(e) => {
            let next = index;
            if (e.key === "ArrowRight") next = (index + 1) % tabs.length;
            else if (e.key === "ArrowLeft")
              next = (index + tabs.length - 1) % tabs.length;
            else if (e.key === "Home") next = 0;
            else if (e.key === "End") next = tabs.length - 1;
            else return;
            e.preventDefault();
            onChange(tabs[next][0]);
            document.getElementById(`${scope}-${tabs[next][0]}`)?.focus();
          }}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
