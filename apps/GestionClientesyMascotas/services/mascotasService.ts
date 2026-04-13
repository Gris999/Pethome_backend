import axios from "axios";
import type {
  ClienteOption,
  EspecieOption,
  Mascota,
  MascotaPayload,
  RazaOption,
} from "../types/mascota";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api/gestion/clientes",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const getMascotas = async (): Promise<Mascota[]> => {
  const { data } = await api.get<Mascota[]>("/mascotas/");
  return data;
};

export const getMascotaById = async (id: number): Promise<Mascota> => {
  const { data } = await api.get<Mascota>(`/mascotas/${id}/`);
  return data;
};

export const createMascota = async (payload: MascotaPayload): Promise<Mascota> => {
  const { data } = await api.post<Mascota>("/mascotas/", payload);
  return data;
};

export const updateMascota = async (
  id: number,
  payload: Partial<MascotaPayload>
): Promise<Mascota> => {
  const { data } = await api.patch<Mascota>(`/mascotas/${id}/`, payload);
  return data;
};

export const deleteMascota = async (id: number): Promise<void> => {
  await api.delete(`/mascotas/${id}/`);
};

export const getClientes = async (): Promise<ClienteOption[]> => {
  const { data } = await api.get<ClienteOption[]>("/usuarios/");
  return data;
};

export const getEspecies = async (): Promise<EspecieOption[]> => {
  const { data } = await api.get<EspecieOption[]>("/especies/");
  return data;
};

export const getRazas = async (especieId?: number): Promise<RazaOption[]> => {
  const url = especieId ? `/razas/?especie_id=${especieId}` : "/razas/";
  const { data } = await api.get<RazaOption[]>(url);
  return data;
};