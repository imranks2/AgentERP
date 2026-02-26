import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { NAV_ITEMS } from '../utils/constants';

/**
 * ⌘K Command Palette — global search + navigation overlay.
 *
 * @param {Object}   props
 * @param {boolean}  props.open     - Controlled open state
 * @param {Function} props.onClose  - Close callback
 * @param {Array}    [props.extra]  - Additional command items:
 *   [{ id, label, description?, icon?, section?, action? }]
 */
export default function CommandPalette({ open, onClose, extra = [] }) {
  const [query, setQuery] = useState('');
  const [activeIdx, setActiveIdx] = useState(0);
  const inputRef = useRef(null);
  const listRef = useRef(null);
  const navigate = useNavigate();

  // Build command list from nav items + extras
  const commands = React.useMemo(() => {
    const nav = NAV_ITEMS
      .filter((it) => it.key) // skip dividers / labels
      .map((it) => ({
        id: it.key,
        label: it.label,
        description: `Go to ${it.label}`,
        section: 'Navigation',
        action: () => navigate(it.path),
      }));

    return [...nav, ...extra];
  }, [extra, navigate]);

  // Filter by query
  const filtered = React.useMemo(() => {
    if (!query.trim()) return commands;
    const q = query.toLowerCase();
    return commands.filter(
      (c) =>
        c.label.toLowerCase().includes(q) ||
        (c.description && c.description.toLowerCase().includes(q))
    );
  }, [commands, query]);

  // Group by section
  const grouped = React.useMemo(() => {
    const map = new Map();
    filtered.forEach((c) => {
      const sec = c.section || 'Actions';
      if (!map.has(sec)) map.set(sec, []);
      map.get(sec).push(c);
    });
    return map;
  }, [filtered]);

  // Flatten for keyboard nav
  const flatList = React.useMemo(() => {
    const arr = [];
    grouped.forEach((items) => arr.push(...items));
    return arr;
  }, [grouped]);

  // Reset on open
  useEffect(() => {
    if (open) {
      setQuery('');
      setActiveIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Clamp active index
  useEffect(() => {
    if (activeIdx >= flatList.length) setActiveIdx(Math.max(0, flatList.length - 1));
  }, [flatList.length, activeIdx]);

  // Scroll active item into view
  useEffect(() => {
    const el = listRef.current?.querySelector('.cmd-item.active');
    el?.scrollIntoView({ block: 'nearest' });
  }, [activeIdx]);

  const run = useCallback(
    (cmd) => {
      if (cmd?.action) cmd.action();
      onClose();
    },
    [onClose]
  );

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIdx((i) => (i + 1) % Math.max(flatList.length, 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIdx((i) => (i - 1 + flatList.length) % Math.max(flatList.length, 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      run(flatList[activeIdx]);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  };

  if (!open) return null;

  let itemCounter = 0;

  return (
    <div className="cmd-backdrop" onClick={onClose}>
      <div
        className="cmd-dialog"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Command palette"
      >
        {/* Search input */}
        <div className="cmd-input-wrap">
          <Search size={18} />
          <input
            ref={inputRef}
            className="cmd-input"
            placeholder="Type a command or search…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActiveIdx(0);
            }}
            onKeyDown={handleKeyDown}
          />
          <kbd className="cmd-kbd">esc</kbd>
        </div>

        {/* Results */}
        <div className="cmd-results" ref={listRef}>
          {flatList.length === 0 && (
            <div className="cmd-empty">No results found</div>
          )}
          {Array.from(grouped.entries()).map(([section, items]) => (
            <div key={section}>
              <div className="cmd-group-label">{section}</div>
              {items.map((cmd) => {
                const idx = itemCounter++;
                return (
                  <div
                    key={cmd.id}
                    className={`cmd-item ${idx === activeIdx ? 'active' : ''}`}
                    onMouseEnter={() => setActiveIdx(idx)}
                    onClick={() => run(cmd)}
                  >
                    <div className="cmd-item-icon">
                      {cmd.icon || <ArrowRight size={16} />}
                    </div>
                    <div className="cmd-item-text">
                      <div className="cmd-item-label">{cmd.label}</div>
                      {cmd.description && (
                        <div className="cmd-item-desc">{cmd.description}</div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>

        {/* Footer hints */}
        <div className="cmd-footer">
          <div className="cmd-footer-hint">
            <kbd className="cmd-kbd">↑↓</kbd> navigate
          </div>
          <div className="cmd-footer-hint">
            <kbd className="cmd-kbd">↵</kbd> select
          </div>
          <div className="cmd-footer-hint">
            <kbd className="cmd-kbd">esc</kbd> close
          </div>
        </div>
      </div>
    </div>
  );
}
