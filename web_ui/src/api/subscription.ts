import http from './http'

export interface Subscription {
  id: string
  mp_id: string
  name: string
  mp_name: string
  mp_cover: string
  mp_intro: string
  status: number
  sync_time: string
  rss_url: string
  article_count: number
}

export interface SubscriptionListResult {
  code: number
  data: {
    list: Subscription[]
    total: number
  }
}

export interface AddSubscriptionParams {
  mp_name: string
  mp_id: string
  avatar: string
  mp_intro?: string
}

export interface MpItem {
  mp_id: string
  mp_name: string
  avatar: string
}

export interface MpSearchResult {
  code: number
  data: MpItem[]
}

export interface FeaturedArticleTask {
  task_id: string
  url: string
  status: 'pending' | 'running' | 'success' | 'failed'
  message: string
  id?: string
  mp_id?: string
  mp_name?: string
  title?: string
  created?: boolean
}

const normalizePageSize = (pageSize?: number) => {
  if (!pageSize || Number.isNaN(pageSize)) {
    return 10
  }
  return Math.min(Math.max(pageSize, 1), 500)
}

const buildSubscriptionQuery = (params?: { page?: number; pageSize?: number; kw?: string; status?: number }) => {
  const safePageSize = normalizePageSize(params?.pageSize)
  const safePage = Math.max(params?.page || 0, 0)
  const apiParams = {
    offset: safePage * safePageSize,
    limit: safePageSize,
    kw: (params?.kw || "").trim(),
    ...(params?.status !== undefined && params?.status !== null ? { status: params.status } : {})
  }
  return apiParams
}

export const getSubscriptions = (params?: { page?: number; pageSize?: number; kw?: string; status?: number }) => {
  const apiParams = buildSubscriptionQuery(params)
  return http.get<SubscriptionListResult>('/wx/mps', { params: apiParams })
}

export const getAllSubscriptions = async (params?: { kw?: string; status?: number; pageSize?: number }) => {
  const pageSize = normalizePageSize(params?.pageSize || 100)
  let page = 0
  let list: Subscription[] = []

  while (true) {
    const data = await getSubscriptions({
      page,
      pageSize,
      kw: params?.kw,
      status: params?.status
    })
    const current = data?.list || []
    list = list.concat(current)
    if (current.length < pageSize) {
      break
    }
    page += 1
  }

  return list
}

export const getSubscriptionDetail = (mp_id: string) => {
  return http.get<{code: number, data: Subscription}>(`/wx/mps/${mp_id}`)
}

// 添加订阅公众号信息
export const addSubscription = (data: AddSubscriptionParams) => {
  return http.post<{code: number, message: string}>('/wx/mps', data)
}
export const getSubscriptionInfo = (url: string) => {
  return http.post<{code: number, message: string}>(`/wx/mps/by_article?url=${url}`)
}

export const addFeaturedArticle = (data: { url: string }) => {
  return http.post<{code: number, data: FeaturedArticleTask}>('/wx/mps/featured/article', data)
}

export const getFeaturedArticleTaskStatus = (taskId: string) => {
  return http.get<{code: number, data: FeaturedArticleTask}>(`/wx/mps/featured/article/tasks/${taskId}`)
}

export const deleteMpApi = (mp_id: string) => {
  return http.delete<{code: number, message: string}>(`/wx/mps/${mp_id}`)
}

export const deleteSubscription = (mp_id: string) => {
  return http.delete<{code: number, message: string}>(`/wx/mps/${mp_id}`)
}

// 更新订阅公众号文章列表 
export const UpdateMps = (mp_id: string,params: { start_page?: number; end_page?: number }) => {
   const apiParams = {
    start_page: (params?.start_page || 0),
    end_page: params?.end_page || 1
  }
  return http.get<{code: number, message: string, task_id?: string, status?: string}>(`/wx/mps/update/${mp_id||'all'}?start_page=${apiParams.start_page}&end_page=${apiParams.end_page}`)
}

export const getUpdateMpsTaskStatus = (taskId: string) => {
  return http.get<{code: number, data: any}>(`/wx/mps/update/tasks/${taskId}`)
}

// 更新订阅公众号信息
export const updateSubscription = (mp_id: string, data: Partial<Subscription>) => {
  return http.put<{code: number, message: string}>(`/wx/mps/${mp_id}`, data)
}

// 切换公众号状态（启用/禁用）
export const toggleMpStatus = (mp_id: string, status: number) => {
  return http.put<{code: number, message: string}>(`/wx/mps/${mp_id}`, { status })
}

export const searchBiz = (kw: string, params: { page?: number; pageSize?: number }) => {
  const apiParams = {
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<SubscriptionListResult>(`/wx/mps/search/${kw}`,{ params: apiParams })
}

// 搜索公众号(不分页)
export const searchMps = (kw: string, params: { page?: number; pageSize?: number }) => {
  const apiParams = {
    kw:kw||"",
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<SubscriptionListResult>(`/wx/mps`,{ params: apiParams })
}
