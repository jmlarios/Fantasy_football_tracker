import api from './api';

export interface Player {
  id: number;
  name: string;
  team: string;
  position: string;
  price: number;
  is_active?: boolean;
}

export interface TransferOffer {
  id: number;
  from_team: {
    id: number;
    name: string;
    user_name: string;
  };
  to_team: {
    id: number;
    name: string;
    user_name: string;
  };
  player_requested: Player & { team: string };
  offer_type: 'money' | 'player_exchange';
  money_offered?: number;
  player_offered?: Player & { team: string };
  status: string;
  created_at: string;
  expires_at: string;
  time_until_expiry: string;
  is_expired: boolean;
}

export interface LeagueTeam {
  id: number;
  team_name: string;
  user_name: string;
  user_id: number;
  league_points: number;
  league_rank: number;
  is_current_user: boolean;
  players: Player[];
}

export const transferService = {
  // Free Agent Transfers
  async getAvailablePlayers(
    leagueId: number,
    filters?: {
      position?: string;
      search?: string;
      min_price?: number;
      max_price?: number;
    }
  ) {
    const params = new URLSearchParams();
    if (filters?.position) params.append('position', filters.position);
    if (filters?.search) params.append('search', filters.search);
    if (filters?.min_price !== undefined) params.append('min_price', filters.min_price.toString());
    if (filters?.max_price !== undefined) params.append('max_price', filters.max_price.toString());

    const response = await api.get(
      `/leagues/${leagueId}/players/available?${params.toString()}`
    );
    return response.data;
  },

  async executeFreeAgentTransfer(
    leagueId: number,
    teamId: number,
    playerInId: number,
    playerOutId?: number // Made optional
  ) {
    const response = await api.post(
      `/leagues/${leagueId}/teams/${teamId}/transfers/free-agent`,
      {
        player_in_id: playerInId,
        player_out_id: playerOutId, // Will be undefined if not provided
      }
    );
    return response.data;
  },

  // User-to-User Transfers
  async createTransferOffer(
    leagueId: number,
    data: {
      to_team_id: number;
      player_id: number;
      offer_type: 'money' | 'player_exchange';
      money_offered?: number;
      player_offered_id?: number;
      player_out_id?: number; // Player to drop for money offers
    }
  ) {
    const response = await api.post(`/leagues/${leagueId}/transfers/offers`, data);
    return response.data;
  },

  async getTransferOffers(
    leagueId: number,
    teamId: number,
    direction: 'received' | 'sent' = 'received'
  ) {
    const response = await api.get(
      `/leagues/${leagueId}/teams/${teamId}/transfers/offers?direction=${direction}`
    );
    return response.data;
  },

  async acceptTransferOffer(leagueId: number, offerId: number) {
    const response = await api.put(
      `/leagues/${leagueId}/transfers/offers/${offerId}/accept`
    );
    return response.data;
  },

  async rejectTransferOffer(leagueId: number, offerId: number) {
    const response = await api.put(
      `/leagues/${leagueId}/transfers/offers/${offerId}/reject`
    );
    return response.data;
  },

  async cancelTransferOffer(leagueId: number, offerId: number) {
    const response = await api.delete(`/leagues/${leagueId}/transfers/offers/${offerId}`);
    return response.data;
  },

  async getLeagueTeams(leagueId: number) {
    const response = await api.get(`/leagues/${leagueId}/teams`);
    return response.data;
  },

  async getFantasyTeamLeagues(teamId: number) {
    const response = await api.get(`/fantasy-teams/${teamId}/leagues`);
    return response.data;
  },
};
