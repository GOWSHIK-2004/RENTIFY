import { Star } from 'lucide-react'

/** Read-only stars, or clickable when `onChange` is given. */
export default function StarRating({ value = 0, onChange, size = 'h-4 w-4' }) {
  return (
    <div className="inline-flex items-center gap-0.5" role={onChange ? 'radiogroup' : 'img'} aria-label={`${value} out of 5 stars`}>
      {[1, 2, 3, 4, 5].map((star) => {
        const icon = (
          <Star
            className={`${size} ${star <= Math.round(value) ? 'fill-primary text-primary' : 'text-slate-300'}`}
            aria-hidden="true"
          />
        )
        return onChange ? (
          <button
            key={star}
            type="button"
            role="radio"
            aria-checked={star === value}
            aria-label={`${star} star${star > 1 ? 's' : ''}`}
            onClick={() => onChange(star)}
          >
            {icon}
          </button>
        ) : (
          <span key={star}>{icon}</span>
        )
      })}
    </div>
  )
}
