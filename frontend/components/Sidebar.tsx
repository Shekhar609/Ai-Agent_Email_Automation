"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { Activity, Clock, FileText, Inbox, Send, Settings } from "lucide-react";

const items = [
  { href: "/inbox", label: "Inbox", icon: Inbox },
  { href: "/drafts", label: "Drafts", icon: FileText },
  { href: "/sent", label: "Sent", icon: Send },
  { href: "/followups", label: "Follow-ups", icon: Clock },
  { href: "/activity", label: "Activity", icon: Activity },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="w-56 shrink-0 border-r border-neutral-200 bg-white px-3 py-6">
      <div className="px-3 mb-6">
        <h1 className="text-sm font-semibold tracking-tight">Email Automation</h1>
        <p className="text-xs text-neutral-500">v0.1.0</p>
      </div>
      <nav className="space-y-1">
        {items.map((item) => {
          const active = path === item.href || path.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors",
                active
                  ? "bg-neutral-900 text-white"
                  : "text-neutral-700 hover:bg-neutral-100",
              )}
            >
              <Icon size={16} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
