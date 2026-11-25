import { Link } from 'react-router-dom'
import { ArrowRight, CalendarDays, PackageCheck, Search, ShieldCheck, Wallet } from 'lucide-react'
import { categoryApi, productApi } from '../../api'
import Button from '../../components/Button'
import CategoryIcon from '../../components/CategoryIcon'
import FaqList from '../../components/FaqList'
import { EmptyState, ErrorState, PageLoader } from '../../components/Feedback'
import ProductCard from '../../components/ProductCard'
import useFetch from '../../hooks/useFetch'
import { imageSrc } from '../../utils/format'

const STEPS = [
  { icon: Search, title: 'Find your gear', text: 'Browse cameras, consoles, laptops, drones and more.' },
  { icon: CalendarDays, title: 'Pick your dates', text: 'Choose pickup and return dates and see the price instantly.' },
  { icon: PackageCheck, title: 'Confirm and collect', text: 'Book in a minute, then pick up your inspected equipment.' },
  { icon: Wallet, title: 'Return and relax', text: 'Bring it back on time. No storage, no resale, no worries.' },
]

export default function Home() {
  const categories = useFetch(() => categoryApi.list(), [])
  const featured = useFetch(() => productApi.featured(), [])

  return (
    <>
      <section className="border-b border-line bg-white">
        <div className="mx-auto grid max-w-7xl items-center gap-10 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:py-24">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-primary">Rent More. Own Less.</p>
            <h1 className="mt-3 text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
              Professional equipment, without the price tag.
            </h1>
            <p className="mt-4 max-w-xl text-lg text-muted">
              Rent cameras, drones, laptops and more by the day. Pay for the days you need instead of buying gear you
              will use once.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button to="/products" size="lg">
                Browse equipment <ArrowRight className="h-5 w-5" />
              </Button>
              <Button to="/faq" size="lg" variant="secondary">
                How it works
              </Button>
            </div>
            <p className="mt-6 flex items-center gap-2 text-sm text-muted">
              <ShieldCheck className="h-4 w-4 text-primary" aria-hidden="true" />
              Every item is owned, inspected and maintained by Rentify.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {featured.data?.slice(0, 4).map((product) => (
              <Link
                key={product.id}
                to={`/products/${product.id}`}
                className="overflow-hidden rounded-xl border border-line bg-surface p-3 transition-shadow hover:shadow-md"
              >
                <img
                  src={imageSrc(product.image_url)}
                  alt=""
                  className="aspect-[4/3] w-full rounded-lg object-cover"
                />
                <p className="mt-2 line-clamp-1 text-sm font-medium">{product.name}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6" aria-labelledby="categories-heading">
        <h2 id="categories-heading" className="text-2xl font-bold">
          Popular categories
        </h2>
        {categories.loading ? (
          <PageLoader />
        ) : categories.error ? (
          <ErrorState message={categories.error} onRetry={categories.reload} />
        ) : (
          <ul className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {categories.data.map((category) => (
              <li key={category.id}>
                <Link
                  to={`/products?category=${category.slug}`}
                  className="flex h-full flex-col items-start gap-3 rounded-xl border border-line bg-white p-5 transition-shadow hover:shadow-md"
                >
                  <span className="rounded-lg bg-orange-50 p-2.5 text-primary">
                    <CategoryIcon slug={category.slug} />
                  </span>
                  <span className="font-semibold">{category.name}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mx-auto max-w-7xl px-4 sm:px-6" aria-labelledby="featured-heading">
        <div className="flex items-end justify-between">
          <h2 id="featured-heading" className="text-2xl font-bold">
            Featured equipment
          </h2>
          <Link to="/products" className="text-sm font-medium text-primary hover:underline">
            View all
          </Link>
        </div>
        {featured.loading ? (
          <PageLoader />
        ) : featured.error ? (
          <ErrorState message={featured.error} onRetry={featured.reload} />
        ) : featured.data.length === 0 ? (
          <div className="mt-6">
            <EmptyState title="Nothing featured yet" description="Check back soon." />
          </div>
        ) : (
          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {featured.data.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </section>

      <section className="mx-auto mt-20 max-w-7xl px-4 sm:px-6" aria-labelledby="how-heading">
        <h2 id="how-heading" className="text-center text-2xl font-bold">
          How renting works
        </h2>
        <ol className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, index) => (
            <li key={step.title} className="rounded-xl border border-line bg-white p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-50 text-primary">
                <step.icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <h3 className="mt-4 font-semibold">
                {index + 1}. {step.title}
              </h3>
              <p className="mt-1 text-sm text-muted">{step.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="mx-auto mt-20 max-w-3xl px-4 sm:px-6" aria-labelledby="faq-heading">
        <h2 id="faq-heading" className="text-center text-2xl font-bold">
          Frequently asked questions
        </h2>
        <div className="mt-6">
          <FaqList />
        </div>
      </section>
    </>
  )
}
