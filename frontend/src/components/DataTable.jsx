import React, { useState, useMemo, useCallback } from 'react';
import {
  Search, ChevronUp, ChevronDown, ChevronsUpDown,
  ChevronLeft, ChevronRight, Inbox,
} from 'lucide-react';

/**
 * Schema-driven DataTable with search, sort, pagination, batch selection.
 *
 * Props:
 *  columns : [{ key, label, sortable?, render?, primary?, align?, width? }]
 *  data    : array of row objects
 *  loading : boolean
 *  searchable : boolean (default true)
 *  searchPlaceholder : string
 *  paginate : boolean (default true)
 *  pageSize : number (default 10)
 *  selectable : boolean — show checkboxes (default false)
 *  onSelectionChange : (selectedIds[]) => void
 *  rowKey : string — field name to use as unique key (default 'id')
 *  emptyTitle : string
 *  emptyDesc  : string
 *  toolbar    : ReactNode — extra buttons to render in the toolbar
 *  batchActions : ReactNode — rendered when items are selected
 *  onRowClick : (row) => void
 *  defaultSort : { key, dir } (optional)
 *  externalSearch : string (use external search control instead of built-in)
 */
export default function DataTable({
  columns = [],
  data = [],
  loading = false,
  searchable = true,
  searchPlaceholder = 'Search…',
  paginate = true,
  pageSize: initialPageSize = 10,
  selectable = false,
  onSelectionChange,
  rowKey = 'id',
  emptyTitle = 'No data',
  emptyDesc = '',
  toolbar,
  batchActions,
  onRowClick,
  defaultSort,
  externalSearch,
}) {
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState(defaultSort || { key: null, dir: 'asc' });
  const [page, setPage] = useState(1);
  const [pageSize] = useState(initialPageSize);
  const [selected, setSelected] = useState(new Set());

  // Active search string (external or internal)
  const searchStr = externalSearch !== undefined ? externalSearch : search;

  // ── Filter ──
  const filtered = useMemo(() => {
    if (!searchStr) return data;
    const q = searchStr.toLowerCase();
    return data.filter((row) =>
      columns.some(({ key, render }) => {
        const val = row[key];
        if (val == null) return false;
        return String(val).toLowerCase().includes(q);
      }),
    );
  }, [data, searchStr, columns]);

  // ── Sort ──
  const sorted = useMemo(() => {
    if (!sort.key) return filtered;
    const arr = [...filtered];
    arr.sort((a, b) => {
      const av = a[sort.key];
      const bv = b[sort.key];
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === 'number' && typeof bv === 'number') return sort.dir === 'asc' ? av - bv : bv - av;
      return sort.dir === 'asc' ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
    return arr;
  }, [filtered, sort]);

  // ── Paginate ──
  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const paged = paginate ? sorted.slice((safePage - 1) * pageSize, safePage * pageSize) : sorted;

  // Reset page on data/search change
  const handleSearch = (v) => { setSearch(v); setPage(1); };

  // ── Sort toggle ──
  const toggleSort = useCallback((key) => {
    setSort((prev) =>
      prev.key === key
        ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: 'asc' },
    );
  }, []);

  // ── Selection helpers ──
  const allSelected = paged.length > 0 && paged.every((r) => selected.has(r[rowKey]));
  const toggleAll = () => {
    const next = new Set(selected);
    if (allSelected) paged.forEach((r) => next.delete(r[rowKey]));
    else paged.forEach((r) => next.add(r[rowKey]));
    setSelected(next);
    onSelectionChange?.(Array.from(next));
  };
  const toggleRow = (id) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
    onSelectionChange?.(Array.from(next));
  };
  const clearSelection = () => { setSelected(new Set()); onSelectionChange?.([]); };

  // ── Sort icon ──
  const SortIcon = ({ colKey }) => {
    if (sort.key !== colKey) return <ChevronsUpDown size={14} />;
    return sort.dir === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />;
  };

  // ── Skeleton rows ──
  const renderSkeleton = () =>
    Array.from({ length: 5 }).map((_, i) => (
      <tr key={`sk-${i}`} className="dt-skeleton-row">
        {selectable && <td className="checkbox-col"><div className="dt-skeleton" style={{ width: 16, height: 16 }} /></td>}
        {columns.map((col) => (
          <td key={col.key}><div className="dt-skeleton" style={{ width: `${50 + Math.random() * 40}%` }} /></td>
        ))}
      </tr>
    ));

  // ── Page buttons ──
  const pageButtons = useMemo(() => {
    const btns = [];
    const range = 2;
    let start = Math.max(1, safePage - range);
    let end = Math.min(totalPages, safePage + range);
    if (start > 1) { btns.push(1); if (start > 2) btns.push('...'); }
    for (let i = start; i <= end; i++) btns.push(i);
    if (end < totalPages) { if (end < totalPages - 1) btns.push('...'); btns.push(totalPages); }
    return btns;
  }, [safePage, totalPages]);

  return (
    <div className="dt-container">
      {/* Toolbar */}
      {(searchable || toolbar) && externalSearch === undefined && (
        <div className="dt-toolbar">
          {searchable && (
            <div className="dt-search">
              <Search size={16} />
              <input
                placeholder={searchPlaceholder}
                value={search}
                onChange={(e) => handleSearch(e.target.value)}
              />
            </div>
          )}
          {toolbar && <div className="dt-toolbar-actions">{toolbar}</div>}
        </div>
      )}

      {/* Batch bar */}
      {selected.size > 0 && batchActions && (
        <div className="dt-batch-bar">
          <span>{selected.size} selected</span>
          {batchActions}
          <button className="dt-filter-btn" onClick={clearSelection} style={{ marginLeft: 'auto' }}>
            Clear
          </button>
        </div>
      )}

      {/* Table */}
      <div className="dt-table-wrap">
        <table className="dt-table">
          <thead>
            <tr>
              {selectable && (
                <th className="checkbox-col">
                  <input
                    type="checkbox"
                    className="dt-checkbox"
                    checked={allSelected}
                    onChange={toggleAll}
                  />
                </th>
              )}
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`${col.sortable ? 'sortable' : ''} ${sort.key === col.key ? 'sorted' : ''}`}
                  style={{ width: col.width, textAlign: col.align }}
                  onClick={col.sortable ? () => toggleSort(col.key) : undefined}
                >
                  {col.label}
                  {col.sortable && <span className="sort-icon"><SortIcon colKey={col.key} /></span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? renderSkeleton() : paged.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (selectable ? 1 : 0)}>
                  <div className="dt-empty">
                    <Inbox size={40} className="dt-empty-icon" />
                    <div className="dt-empty-title">{emptyTitle}</div>
                    {emptyDesc && <div className="dt-empty-desc">{emptyDesc}</div>}
                  </div>
                </td>
              </tr>
            ) : (
              paged.map((row) => (
                <tr
                  key={row[rowKey]}
                  className={selected.has(row[rowKey]) ? 'selected' : ''}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  style={onRowClick ? { cursor: 'pointer' } : undefined}
                >
                  {selectable && (
                    <td className="checkbox-col" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        className="dt-checkbox"
                        checked={selected.has(row[rowKey])}
                        onChange={() => toggleRow(row[rowKey])}
                      />
                    </td>
                  )}
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={`${col.primary ? 'primary-cell' : ''} ${col.key === '_actions' ? 'actions-cell' : ''}`}
                      style={{ textAlign: col.align }}
                    >
                      {col.render ? col.render(row[col.key], row) : row[col.key] ?? '-'}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {paginate && sorted.length > pageSize && (
        <div className="dt-pagination">
          <div className="dt-pagination-info">
            Showing {(safePage - 1) * pageSize + 1}–{Math.min(safePage * pageSize, sorted.length)} of {sorted.length}
          </div>
          <div className="dt-pagination-controls">
            <button className="dt-page-btn" disabled={safePage <= 1} onClick={() => setPage(safePage - 1)}>
              <ChevronLeft size={16} />
            </button>
            {pageButtons.map((p, i) =>
              p === '...' ? (
                <span key={`e${i}`} className="dt-page-btn" style={{ cursor: 'default' }}>…</span>
              ) : (
                <button key={p} className={`dt-page-btn${p === safePage ? ' active' : ''}`} onClick={() => setPage(p)}>
                  {p}
                </button>
              ),
            )}
            <button className="dt-page-btn" disabled={safePage >= totalPages} onClick={() => setPage(safePage + 1)}>
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
