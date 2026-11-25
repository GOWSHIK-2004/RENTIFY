import { EmptyState } from './Feedback'

/**
 * Simple responsive table. `columns` is [{ header, render(row), className? }].
 * Wide tables scroll sideways on small screens instead of breaking the layout.
 */
export default function DataTable({ columns, rows, emptyTitle = 'Nothing to show', emptyDescription }) {
  if (rows.length === 0) return <EmptyState title={emptyTitle} description={emptyDescription} />
  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-white">
      <table className="min-w-full divide-y divide-line text-left text-sm">
        <thead className="bg-surface text-xs uppercase tracking-wide text-muted">
          <tr>
            {columns.map((column) => (
              <th key={column.header} scope="col" className={`px-4 py-3 font-medium ${column.className ?? ''}`}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((row) => (
            <tr key={row.id} className="align-middle hover:bg-surface/60">
              {columns.map((column) => (
                <td key={column.header} className={`px-4 py-3 ${column.className ?? ''}`}>
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
