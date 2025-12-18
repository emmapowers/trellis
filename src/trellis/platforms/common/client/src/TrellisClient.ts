/** Abstract interface for Trellis client implementations.
 *
 * Both WebSocket (server) and Channel (desktop) clients implement this interface.
 * This allows the common TreeRenderer and widgets to work with any transport.
 */
export interface TrellisClient {
  /** Send an event to the backend to invoke a callback. */
  sendEvent(callbackId: string, args: unknown[]): void;
}
