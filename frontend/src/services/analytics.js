import { analyticsAPI } from './api';

/**
 * Analytics tracker for AI training data collection.
 * Captures user interactions from the frontend.
 */
class Analytics {
  constructor() {
    this.sessionId = this.generateSessionId();
    this.queue = [];
    this.flushInterval = null;
  }

  generateSessionId() {
    return `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  track(eventType, eventAction, properties = {}) {
    const event = {
      event_type: eventType,
      event_action: eventAction,
      event_category: 'frontend',
      properties: {
        ...properties,
        session_id: this.sessionId,
        url: window.location.pathname,
        timestamp: new Date().toISOString(),
      },
    };

    // Fire and forget - don't block UI
    analyticsAPI.track(event).catch(() => {
      // Silently fail for analytics
    });
  }

  pageView(pageName) {
    this.track('page_view', pageName, { page: window.location.pathname });
  }

  buttonClick(buttonName, context = {}) {
    this.track('interaction', `click:${buttonName}`, context);
  }

  formSubmit(formName, success = true) {
    this.track('form', `submit:${formName}`, { success });
  }

  search(query, resultCount = 0) {
    this.track('search', 'search', { query, result_count: resultCount });
  }

  featureUsed(featureName, context = {}) {
    this.track('feature', `use:${featureName}`, context);
  }
}

const analytics = new Analytics();
export default analytics;
