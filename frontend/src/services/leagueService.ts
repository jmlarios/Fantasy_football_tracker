import api from './api';

interface LeagueData {
  name: string;
  description?: string;
  is_private: boolean;
  max_participants: number;
}

interface League {
  id: number;
  name: string;
  description?: string;
  is_private: boolean;
  is_creator: boolean;
  participants: number;
  max_participants: number;
  created_at: string;
  join_code?: string;
}

interface LeagueJoinResult {
  league_id: number;
  league_name: string;
  team_id: number;
  team_name: string;
  participants: number;
}

interface PublicLeague {
  id: number;
  name: string;
  description?: string;
  participants: number;
  max_participants: number;
  created_at: string;
}

interface LeaderboardEntry {
  user_id: number;
  user_name: string;
  team_id: number;
  team_name: string;
  total_points: number;
  rank: number;
  is_current_user: boolean;
}

interface LeaderboardData {
  league: {
    id: number;
    name: string;
    description?: string;
    participants: number;
    max_participants: number;
  };
  leaderboard: LeaderboardEntry[];
  user_rank?: number;
}

const leagueService = {
  createLeague: async (leagueData: LeagueData): Promise<League> => {
    try {
      const response = await api.post('/leagues', leagueData);
      return response.data;
    } catch (error) {
      console.error('Error creating league:', error);
      throw new Error('Failed to create league');
    }
  },

  getUserLeagues: async (): Promise<League[]> => {
    try {
      const response = await api.get('/leagues');
      return response.data || [];
    } catch (error) {
      console.error('Error fetching user leagues:', error);
      // Return empty array instead of throwing to prevent component crashes
      return [];
    }
  },

  getPublicLeagues: async (skip: number = 0, limit: number = 20): Promise<PublicLeague[]> => {
    try {
      const response = await api.get(`/leagues/public?skip=${skip}&limit=${limit}`);
      return response.data || [];
    } catch (error) {
      console.error('Error fetching public leagues:', error);
      return [];
    }
  },

  joinLeagueByCode: async (joinCode: string): Promise<LeagueJoinResult> => {
    try {
      const response = await api.post('/leagues/join', { join_code: joinCode });
      return response.data;
    } catch (error) {
      console.error('Error joining league by code:', error);
      throw new Error('Failed to join league');
    }
  },

  joinLeagueById: async (leagueId: number): Promise<LeagueJoinResult> => {
    try {
      const response = await api.post(`/leagues/${leagueId}/join`);
      return response.data;
    } catch (error) {
      console.error('Error joining league by ID:', error);
      throw new Error('Failed to join league');
    }
  },

  leaveLeague: async (leagueId: number): Promise<{ message: string }> => {
    try {
      const response = await api.delete(`/leagues/${leagueId}/leave`);
      return response.data;
    } catch (error) {
      console.error('Error leaving league:', error);
      throw new Error('Failed to leave league');
    }
  },

  getLeagueLeaderboard: async (leagueId: number): Promise<LeaderboardData> => {
    try {
      const response = await api.get(`/leagues/${leagueId}/leaderboard`);
      return response.data;
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
      throw new Error('Failed to load leaderboard');
    }
  }
};

export default leagueService;
export type { League, LeagueData, LeagueJoinResult, PublicLeague, LeaderboardEntry, LeaderboardData };
