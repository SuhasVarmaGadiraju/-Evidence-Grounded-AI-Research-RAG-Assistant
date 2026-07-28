import React from 'react';
import { Check } from 'lucide-react';

export default function CustomCheckbox({
  checked,
  onChange,
  label,
  disabled = false,
  className = '',
}) {
  const handleChange = (e) => {
    if (disabled) return;
    const nextVal = typeof e.target.checked === 'boolean' ? e.target.checked : !checked;
    if (typeof onChange === 'function') {
      onChange({ target: { checked: nextVal } });
    }
  };

  return (
    <label className={`inline-flex items-center gap-2.5 cursor-pointer select-none ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}>
      <div className="relative">
        <input
          type="checkbox"
          checked={checked}
          onChange={handleChange}
          disabled={disabled}
          className="sr-only"
        />
        <div
          className={`w-4 h-4 rounded border transition-all flex items-center justify-center ${
            checked
              ? 'bg-zinc-900 dark:bg-zinc-100 border-zinc-900 dark:border-zinc-100 text-white dark:text-zinc-900'
              : 'border-theme bg-input hover:border-theme-hover'
          }`}
        >
          {checked && <Check className="w-3 h-3 stroke-[3]" />}
        </div>
      </div>
      {label && <span className="text-xs font-medium text-sub">{label}</span>}
    </label>
  );
}
