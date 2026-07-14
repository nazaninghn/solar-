"use client";

import { useId, useState } from "react";
import { Eye, EyeOff, LucideIcon } from "lucide-react";

export default function FormField({
  label,
  type = "text",
  icon: Icon,
  placeholder,
  autoComplete,
  value,
  onChange,
}: {
  label: string;
  type?: string;
  icon?: LucideIcon;
  placeholder?: string;
  autoComplete?: string;
  value?: string;
  onChange?: (value: string) => void;
}) {
  const id = useId();
  const [show, setShow] = useState(false);
  const isPassword = type === "password";
  const resolvedType = isPassword ? (show ? "text" : "password") : type;

  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-ink mb-2">
        {label}
      </label>
      <div className="relative">
        {Icon && (
          <Icon
            size={17}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
          />
        )}
        <input
          id={id}
          type={resolvedType}
          placeholder={placeholder}
          autoComplete={autoComplete}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          className={`w-full py-3.5 rounded-2xl border border-gray-200 bg-white text-sm text-ink placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-lime-dark/40 focus:border-lime-dark transition-all ${
            Icon ? "pl-11" : "pl-4"
          } ${isPassword ? "pr-11" : "pr-4"}`}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShow((s) => !s)}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-ink transition-colors"
            aria-label={show ? "Hide password" : "Show password"}
          >
            {show ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        )}
      </div>
    </div>
  );
}
