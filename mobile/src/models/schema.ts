// Firebase Firestore Schema Definition for Neighbour In Need

export type UserRole = 'volunteer' | 'requester';
export type RequestStatus = 'open' | 'accepted' | 'completed' | 'cancelled';
export type RequestCategory = 'groceries' | 'medicine' | 'companionship' | 'other';

export interface User {
  uid: string;
  name: string;
  phone: string;
  address: string;
  role: UserRole;
  createdAt: number; // Timestamp
}

export interface HelpRequest {
  id: string;
  requesterId: string;
  title: string;
  description: string;
  category: RequestCategory;
  status: RequestStatus;
  volunteerId?: string | null;
  createdAt: number; // Timestamp
  updatedAt: number; // Timestamp
}

/**
 * Firestore Collections Structure:
 * 
 * /users/{userId} -> User
 * /requests/{requestId} -> HelpRequest
 */
