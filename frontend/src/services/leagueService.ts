import { leagueAPI, throwApiError } from './api';

interface LeagueData {
  name: string;
  description?: string;
  is_private: boolean;
  max_participants: number;
  team_name?: string;
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
      return await leagueAPI.createLeague(leagueData);
    } catch (error) {
      throwApiError(error, 'Failed to create league');
    }
  },

  getUserLeagues: async (): Promise<League[]> => {
    try {
      return await leagueAPI.getUserLeagues();
    } catch (error) {
      console.error('Error fetching user leagues:', error);
      // Return empty array instead of throwing to prevent component crashes
      return [];
    }
  },

  getPublicLeagues: async (skip: number = 0, limit: number = 20): Promise<PublicLeague[]> => {
    try {
      return await leagueAPI.getPublicLeagues(skip, limit);
    } catch (error) {
      console.error('Error fetching public leagues:', error);
      return [];
    }
  },

  joinLeagueByCode: async (joinCode: string, teamName?: string): Promise<LeagueJoinResult> => {
    try {
      return await leagueAPI.joinLeagueByCode(joinCode, teamName);
    } catch (error) {
      throwApiError(error, 'Failed to join league');
    }
  },

  joinLeagueById: async (leagueId: number, teamName?: string): Promise<LeagueJoinResult> => {
    try {
      return await leagueAPI.joinLeagueById(leagueId, teamName);
    } catch (error) {
      throwApiError(error, 'Failed to join league');
    }
  },

  leaveLeague: async (leagueId: number): Promise<{ message: string }> => {
    try {
      return await leagueAPI.leaveLeague(leagueId);
    } catch (error) {
      throwApiError(error, 'Failed to leave league');
    }
  },

  getLeagueLeaderboard: async (leagueId: number): Promise<LeaderboardData> => {
    try {
      return await leagueAPI.getLeagueLeaderboard(leagueId);
    } catch (error) {
      throwApiError(error, 'Failed to load leaderboard');
    }
  },

  updateLeague: async (leagueId: number, data: {
    name?: string;
    description?: string;
    max_participants?: number;
  }): Promise<League> => {
    try {
      return await leagueAPI.updateLeague(leagueId, data);
    } catch (error) {
      throwApiError(error, 'Failed to update league');
    }
  },

  updateTeamName: async (leagueId: number, teamName: string): Promise<{ league_id: number; team_id: number; team_name: string }> => {
    try {
      return await leagueAPI.updateLeagueTeamName(leagueId, teamName);
    } catch (error) {
      throwApiError(error, 'Failed to update team name');
    }
  },

  deleteLeague: async (leagueId: number): Promise<{ message: string }> => {
    try {
      return await leagueAPI.deleteLeague(leagueId);
    } catch (error) {
      throwApiError(error, 'Failed to delete league');
    }
  }
};

export default leagueService;
export type { League, LeagueData, LeagueJoinResult, PublicLeague, LeaderboardEntry, LeaderboardData };
