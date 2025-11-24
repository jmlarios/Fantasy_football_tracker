import axios from 'axios';
import { LoginRequest, RegisterRequest, AuthResponse } from '../types/auth';
import { 
  Player, FantasyTeam, FantasyTeamDetail, CreateTeamRequest, 
  AddPlayerRequest, SetCaptainRequest, TeamValidation 
} from '../types/fantasy';

const resolveBaseUrl = (): string => {
  const envBase = import.meta.env?.VITE_API_BASE_URL;
  if (typeof envBase === 'string' && envBase.trim().length > 0) {
    return envBase.trim();
  }
  return '/api';
};

let API_BASE_URL = resolveBaseUrl();

if (import.meta.env?.DEV && API_BASE_URL === '/api') {
  API_BASE_URL = 'http://localhost:5000';
}

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

const resolveApiErrorMessage = (error: unknown, fallback: string): string => {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string' && detail.trim().length > 0) {
      return detail;
    }
    if (typeof error.message === 'string' && error.message.trim().length > 0) {
      return error.message;
    }
  }
  return fallback;
};

export const throwApiError = (error: unknown, fallback: string): never => {
  const message = resolveApiErrorMessage(error, fallback);
  console.error(fallback, error);
  throw new Error(message);
};

export const authAPI = {
  login: (data: LoginRequest): Promise<AuthResponse> =>
    api.post('/auth/login', data).then(res => res.data),
  
  register: (data: RegisterRequest): Promise<AuthResponse> =>
    api.post('/auth/register', data).then(res => res.data),
  
  logout: () =>
    api.post('/auth/logout').then(res => res.data),
  
  getCurrentUser: () =>
    api.get('/auth/me').then(res => res.data),
};

export const fantasyAPI = {
  // Fantasy Teams
  getTeams: (): Promise<FantasyTeam[]> =>
    api.get('/fantasy-teams').then(res => res.data),
  
  createTeam: (data: CreateTeamRequest): Promise<FantasyTeam> =>
    api.post('/fantasy-teams', data).then(res => res.data),
  
  getTeamDetail: (teamId: number): Promise<FantasyTeamDetail> =>
    api.get(`/fantasy-teams/${teamId}`).then(res => res.data),
  
  addPlayerToTeam: (teamId: number, data: AddPlayerRequest) =>
    api.post(`/fantasy-teams/${teamId}/players`, data).then(res => res.data),
  
  removePlayerFromTeam: (teamId: number, playerId: number) =>
    api.delete(`/fantasy-teams/${teamId}/players/${playerId}`).then(res => res.data),
  
  setCaptain: (teamId: number, data: SetCaptainRequest) =>
    api.post(`/fantasy-teams/${teamId}/captain`, data).then(res => res.data),
  
  validateTeam: (teamId: number): Promise<TeamValidation> =>
    api.get(`/fantasy-teams/${teamId}/validate`).then(res => res.data),
  
  updateTeam: (teamId: number, data: { name: string }) =>
    api.put(`/fantasy-teams/${teamId}`, data).then(res => res.data),
  
  deleteTeam: (teamId: number) =>
    api.delete(`/fantasy-teams/${teamId}`).then(res => res.data),
  
  // Players
  getPlayers: (skip = 0, limit = 50): Promise<Player[]> =>
    api.get(`/players?skip=${skip}&limit=${limit}`).then(res => res.data),
  
  searchPlayers: (params: {
    q?: string;
    team?: string;
    position?: string;
    skip?: number;
    limit?: number;
  }): Promise<Player[]> =>
    api.get('/players/search', { params }).then(res => res.data),
  
  getTeamsInfo: (): Promise<{ name: string }[]> =>
    api.get('/teams').then(res => res.data),
};

export const leagueAPI = {
  // Create a new league
  createLeague: (data: {
    name: string;
    description?: string;
    is_private: boolean;
    max_participants: number;
  }) =>
    api.post('/leagues', data).then(res => res.data),
  
  // Get user's leagues
  getUserLeagues: () =>
    api.get('/leagues').then(res => res.data),
  
  // Get public leagues
  getPublicLeagues: (skip = 0, limit = 20) =>
    api.get(`/leagues/public?skip=${skip}&limit=${limit}`).then(res => res.data),
  
  // Join league by code
  joinLeagueByCode: (joinCode: string, teamName?: string) =>
    api.post('/leagues/join', { join_code: joinCode, team_name: teamName }).then(res => res.data),
  
  // Join league by ID (public leagues)
  joinLeagueById: (leagueId: number, teamName?: string) =>
    api.post(`/leagues/${leagueId}/join`, null, { params: { team_name: teamName } }).then(res => res.data),
  
  // Leave league
  leaveLeague: (leagueId: number) =>
    api.delete(`/leagues/${leagueId}/leave`).then(res => res.data),
  
  // Get league leaderboard
  getLeagueLeaderboard: (leagueId: number) =>
    api.get(`/leagues/${leagueId}/leaderboard`).then(res => res.data),
  
  // Update league (creator only)
  updateLeague: (leagueId: number, data: {
    name?: string;
    description?: string;
    max_participants?: number;
  }) =>
    api.put(`/leagues/${leagueId}`, data).then(res => res.data),
  
  // Get my team in a specific league
  getMyLeagueTeam: (leagueId: number) =>
    api.get(`/leagues/${leagueId}/my-team`).then(res => res.data),
  
  // Update team name in a specific league
  updateLeagueTeamName: (leagueId: number, teamName: string) =>
    api.patch(`/leagues/${leagueId}/my-team`, { team_name: teamName }).then(res => res.data),
};

export default api;
