import React, { useState, useEffect, useCallback, useRef } from 'react';
import { eventsAPI } from '../services/api';
import { Bell, Check, CheckCheck } from 'lucide-react';

/**
 * Notification bell with dropdown — shows unread count and recent notifications.
 */
export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const ref = useRef(null);

  const loadCount = useCallback(async () => {
    try {
      const res = await eventsAPI.unreadCount();
      setUnreadCount(res.data.unread_count);
    } catch (err) { /* ignore */ }
  }, []);

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const res = await eventsAPI.notifications({ per_page: 15 });
      setNotifications(res.data.notifications || []);
      setUnreadCount(res.data.unread_count);
    } catch (err) { /* ignore */ }
    setLoading(false);
  }, []);

  // Poll unread count every 30s
  useEffect(() => {
    loadCount();
    const interval = setInterval(loadCount, 30000);
    return () => clearInterval(interval);
  }, [loadCount]);

  // Load notifications when dropdown opens
  useEffect(() => {
    if (open) loadNotifications();
  }, [open, loadNotifications]);

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleMarkRead = async (id) => {
    try {
      await eventsAPI.markRead(id);
      setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) { /* ignore */ }
  };

  const handleMarkAllRead = async () => {
    try {
      await eventsAPI.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) { /* ignore */ }
  };

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <div className="notification-bell-wrapper" ref={ref}>
      <button
        className="notification-bell-btn"
        onClick={() => setOpen((o) => !o)}
        title="Notifications"
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span className="notification-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
        )}
      </button>

      {open && (
        <div className="notification-dropdown">
          <div className="notification-header">
            <span className="notification-title">Notifications</span>
            {unreadCount > 0 && (
              <button className="btn btn-sm btn-link" onClick={handleMarkAllRead}>
                <CheckCheck size={14} /> Mark all read
              </button>
            )}
          </div>

          <div className="notification-list">
            {loading && <div className="notification-empty">Loading…</div>}
            {!loading && notifications.length === 0 && (
              <div className="notification-empty">No notifications yet</div>
            )}
            {notifications.map((n) => (
              <div
                key={n.id}
                className={`notification-item ${n.is_read ? 'read' : 'unread'}`}
                onClick={() => !n.is_read && handleMarkRead(n.id)}
              >
                <div className="notification-item-content">
                  <div className="notification-item-title">{n.title}</div>
                  <div className="notification-item-message">{n.message}</div>
                  <div className="notification-item-time">{timeAgo(n.created_at)}</div>
                </div>
                {!n.is_read && (
                  <div className="notification-item-dot" title="Unread" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
