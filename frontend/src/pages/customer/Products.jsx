import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search } from 'lucide-react'
import { categoryApi, productApi } from '../../api'
import Button from '../../components/Button'
import { EmptyState, ErrorState, PageLoader } from '../../components/Feedback'
import Input from '../../components/Input'
import Pagination from '../../components/Pagination'
import ProductCard from '../../components/ProductCard'
import useFetch from '../../hooks/useFetch'

const PAGE_SIZE = 12

export default function Products() {
  const [params, setParams] = useSearchParams()
  const categories = useFetch(() => categoryApi.list(), [])

  // The URL is the source of truth, so filters survive reloads and can be shared.
  const q = params.get('q') ?? ''
  const category = params.get('category') ?? ''
  const minPrice = params.get('min_price') ?? ''
  const maxPrice = params.get('max_price') ?? ''
  const sort = params.get('sort') ?? 'newest'
  const page = Number(params.get('page') ?? 1)

  // Text boxes keep local state until the filters are applied.
  const [draft, setDraft] = useState({ q, minPrice, maxPrice })
  useEffect(() => setDraft({ q, minPrice, maxPrice }), [q, minPrice, maxPrice])

  const update = (changes, resetPage = true) => {
    const next = new URLSearchParams(params)
    Object.entries(changes).forEach(([key, value]) => (value ? next.set(key, value) : next.delete(key)))
    if (resetPage) next.delete('page')
    setParams(next)
  }

  const applyFilters = (event) => {
    event.preventDefault()
    update({ q: draft.q.trim(), min_price: draft.minPrice, max_price: draft.maxPrice })
  }

  const products = useFetch(
    () =>
      productApi.list({
        q: q || undefined,
        category: category || undefined,
        min_price: minPrice || undefined,
        max_price: maxPrice || undefined,
        sort,
        page,
        page_size: PAGE_SIZE,
      }),
    [q, category, minPrice, maxPrice, sort, page],
  )

  const hasFilters = q || category || minPrice || maxPrice

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold">Browse equipment</h1>

      <div className="mt-6 grid gap-8 lg:grid-cols-[16rem_1fr]">
        <aside>
          <form onSubmit={applyFilters} className="space-y-4 rounded-xl border border-line bg-white p-4">
            <Input
              label="Search"
              type="search"
              placeholder="Name or brand"
              value={draft.q}
              onChange={(event) => setDraft({ ...draft, q: event.target.value })}
            />
            <Input
              as="select"
              label="Category"
              value={category}
              onChange={(event) => update({ category: event.target.value })}
            >
              <option value="">All categories</option>
              {categories.data?.map((item) => (
                <option key={item.id} value={item.slug}>
                  {item.name}
                </option>
              ))}
            </Input>
            <fieldset>
              <legend className="mb-1 text-sm font-medium">Daily price (₹)</legend>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  min="0"
                  placeholder="Min"
                  aria-label="Minimum daily price"
                  value={draft.minPrice}
                  onChange={(event) => setDraft({ ...draft, minPrice: event.target.value })}
                />
                <span className="text-muted">to</span>
                <Input
                  type="number"
                  min="0"
                  placeholder="Max"
                  aria-label="Maximum daily price"
                  value={draft.maxPrice}
                  onChange={(event) => setDraft({ ...draft, maxPrice: event.target.value })}
                />
              </div>
            </fieldset>
            <Button type="submit" className="w-full">
              <Search className="h-4 w-4" /> Apply filters
            </Button>
            {hasFilters && (
              <Button type="button" variant="ghost" size="sm" className="w-full" onClick={() => setParams({})}>
                Clear all
              </Button>
            )}
          </form>
        </aside>

        <section aria-live="polite">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-muted">
              {products.data ? `${products.data.total} item${products.data.total === 1 ? '' : 's'}` : ' '}
            </p>
            <Input
              as="select"
              aria-label="Sort by"
              value={sort}
              onChange={(event) => update({ sort: event.target.value === 'newest' ? '' : event.target.value })}
            >
              <option value="newest">Newest first</option>
              <option value="price_asc">Price: low to high</option>
              <option value="price_desc">Price: high to low</option>
            </Input>
          </div>

          <div className="mt-4">
            {products.loading ? (
              <PageLoader />
            ) : products.error ? (
              <ErrorState message={products.error} onRetry={products.reload} />
            ) : products.data.items.length === 0 ? (
              <EmptyState
                title="No equipment found"
                description="Try a different search or clear your filters."
                action={
                  hasFilters && (
                    <Button variant="secondary" onClick={() => setParams({})}>
                      Clear filters
                    </Button>
                  )
                }
              />
            ) : (
              <>
                <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                  {products.data.items.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
                <Pagination
                  page={products.data.page}
                  pages={products.data.pages}
                  onChange={(next) => update({ page: String(next) }, false)}
                />
              </>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
