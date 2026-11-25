import { Link } from 'react-router-dom'
import { Star } from 'lucide-react'
import { formatMoney, imageSrc } from '../utils/format'
import Button from './Button'

export default function ProductCard({ product }) {
  return (
    <article className="group flex flex-col overflow-hidden rounded-xl border border-line bg-white shadow-sm transition-shadow hover:shadow-md">
      <Link to={`/products/${product.id}`} className="block aspect-[4/3] overflow-hidden bg-slate-100">
        <img
          src={imageSrc(product.image_url)}
          alt={product.name}
          loading="lazy"
          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
      </Link>
      <div className="flex flex-1 flex-col p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-muted">
          {product.brand} · {product.category.name}
        </p>
        <h3 className="mt-1 line-clamp-2 font-semibold">{product.name}</h3>
        <div className="mt-1 flex items-center gap-1 text-sm text-muted">
          <Star className="h-4 w-4 fill-primary text-primary" aria-hidden="true" />
          {product.average_rating ? (
            <span>
              {product.average_rating.toFixed(1)} ({product.review_count})
            </span>
          ) : (
            <span>No reviews yet</span>
          )}
        </div>
        <div className="mt-auto flex items-end justify-between gap-2 pt-4">
          <p>
            <span className="text-lg font-bold">{formatMoney(product.daily_price)}</span>
            <span className="text-sm text-muted"> / day</span>
          </p>
          <Button to={`/products/${product.id}`} size="sm" variant="secondary">
            View details
          </Button>
        </div>
      </div>
    </article>
  )
}
