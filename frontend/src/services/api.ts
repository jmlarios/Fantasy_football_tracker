import axios from 'axios';
import { LoginRequest, RegisterRequest, AuthResponse } from '../types/auth';
import { 
  Player, FantasyTeam, FantasyTeamDetail, CreateTeamRequest, 
  AddPlayerRequest, SetCaptainRequest, TeamValidation 
} from '../types/fantasy';

const API_BASE_URL = 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

export default api;
