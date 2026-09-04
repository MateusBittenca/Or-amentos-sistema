export function Button({
  children,
  variant = 'primary',
  className = '',
  loading = false,
  disabled,
  type = 'button',
  ...props
}) {
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-blue-50 text-blue-800 hover:bg-blue-100',
    outline: 'border border-blue-600 text-blue-700 bg-white hover:bg-blue-50',
    danger: 'text-red-600 hover:bg-red-50',
  }
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-60 ${variants[variant] || variants.primary} ${className}`}
      {...props}
    >
      {loading ? <i className="fas fa-spinner fa-spin mr-2" /> : null}
      {children}
    </button>
  )
}

export function Card({ children, className = '' }) {
  return <div className={`bg-white rounded-xl shadow-md ${className}`}>{children}</div>
}

export function EmptyState({ icon = 'fa-hard-hat', title, text }) {
  return (
    <div className="text-center py-10 text-gray-500">
      <i className={`fas ${icon} text-3xl text-blue-400 mb-3`} />
      {title ? <p className="font-medium text-gray-700">{title}</p> : null}
      {text ? <p className="text-sm mt-1">{text}</p> : null}
    </div>
  )
}

export function StatusPill({ paid }) {
  return paid ? (
    <span className="px-3 py-1 text-xs rounded-full font-medium bg-green-100 text-green-800">Pago</span>
  ) : (
    <span className="px-3 py-1 text-xs rounded-full font-medium bg-yellow-100 text-yellow-800">Pendente</span>
  )
}

export function Kpi({ label, value, hint, icon }) {
  return (
    <Card className="p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{label}</p>
          <p className="text-2xl font-bold text-gray-800">{value}</p>
          {hint ? <p className="text-xs text-gray-500 mt-1">{hint}</p> : null}
        </div>
        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
          <i className={`fas ${icon}`} />
        </div>
      </div>
    </Card>
  )
}

export function Modal({ open, title, onClose, children, footer }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-40 bg-black bg-opacity-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
          <button type="button" className="text-gray-500 hover:text-gray-700" onClick={onClose}>
            <i className="fas fa-times" />
          </button>
        </div>
        <div className="p-5">{children}</div>
        {footer ? <div className="px-5 py-4 border-t flex justify-end gap-2">{footer}</div> : null}
      </div>
    </div>
  )
}

export function Field({ label, children }) {
  return (
    <label className="block mb-3">
      <span className="block text-sm text-gray-600 mb-1">{label}</span>
      {children}
    </label>
  )
}

export function inputClass() {
  return 'input-focus w-full px-3 py-2 border rounded-lg'
}
