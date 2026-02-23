import { type ReactNode } from 'react'
import React from 'react'

// ── Card ───────────────────────────────────────────────────────────────────
export function Card({ children, className = '', ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`bg-white border border-gray-200 rounded-xl ${className}`} {...props}>
      {children}
    </div>
  )
}

// ── Badge ──────────────────────────────────────────────────────────────────
const badgeColors: Record<string, string> = {
  pending:   'bg-gray-100 text-gray-500',
  running:   'bg-blue-50 text-blue-600',
  completed: 'bg-green-50 text-green-600',
  failed:    'bg-red-50 text-red-600',
  cancelled: 'bg-yellow-50 text-yellow-700',
  skipped:   'bg-gray-100 text-gray-400',
}

export function Badge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium ${
        badgeColors[status] ?? 'bg-gray-100 text-gray-500'
      }`}
    >
      {status}
    </span>
  )
}

// ── Button ─────────────────────────────────────────────────────────────────
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost' | 'danger'
  size?: 'sm' | 'md'
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  ...props
}: ButtonProps) {
  const base = 'inline-flex items-center gap-2 font-medium rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed'
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    ghost:   'bg-transparent hover:bg-gray-100 text-gray-500 hover:text-gray-900',
    danger:  'bg-transparent hover:bg-red-50 text-gray-400 hover:text-red-600',
  }
  const sizes = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-5 py-2.5 text-base',
  }
  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  )
}

// ── Input ──────────────────────────────────────────────────────────────────
export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`bg-white border border-gray-200 rounded-lg px-3.5 py-2.5 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors w-full ${props.className ?? ''}`}
    />
  )
}

// ── Select ─────────────────────────────────────────────────────────────────
export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={`bg-white border border-gray-200 rounded-lg px-3.5 py-2.5 text-base text-gray-900 focus:outline-none focus:border-blue-500 transition-colors w-full ${props.className ?? ''}`}
    />
  )
}

// ── PageHeader ─────────────────────────────────────────────────────────────
export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="flex items-start justify-between mb-8">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">{title}</h1>
        {subtitle && <p className="text-base text-gray-500 mt-1">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}

// ── Spinner ────────────────────────────────────────────────────────────────
export function Spinner({ size = 16 }: { size?: number }) {
  return (
    <svg
      className="animate-spin text-blue-500"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  )
}

// ── EmptyState ─────────────────────────────────────────────────────────────
export function EmptyState({ message, action }: { message: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <p className="text-gray-400 text-base mb-4">{message}</p>
      {action}
    </div>
  )
}
