import { getToken } from './request'

const BASE_URL = 'https://baby.mx.yn.cn/api/v1'

export interface UploadResult {
  code: number
  message: string
  data: {
    url: string
    file_id: string
    file_name: string
    file_size: number
  }
}

// Upload single file
export function uploadFile(filePath: string, type: 'image' | 'file' = 'image'): Promise<UploadResult> {
  return new Promise((resolve, reject) => {
    const token = getToken()
    uni.uploadFile({
      url: BASE_URL + '/upload',
      filePath,
      name: 'file',
      formData: { type },
      header: {
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success(res) {
        try {
          const data = JSON.parse(res.data) as UploadResult
          if (data.code === 0) {
            resolve(data)
          } else {
            uni.showToast({ title: data.message || '上传失败', icon: 'none' })
            reject(new Error(data.message))
          }
        } catch {
          reject(new Error('解析上传结果失败'))
        }
      },
      fail(err) {
        uni.showToast({ title: '上传失败，请重试', icon: 'none' })
        reject(err)
      }
    })
  })
}

// Upload multiple files sequentially
export async function uploadMultipleFiles(filePaths: string[], type: 'image' | 'file' = 'image'): Promise<UploadResult[]> {
  const results: UploadResult[] = []
  for (const filePath of filePaths) {
    const result = await uploadFile(filePath, type)
    results.push(result)
  }
  return results
}

// Choose and upload image from album/camera
export function chooseAndUploadImage(sourceType: ('album' | 'camera')[] = ['album', 'camera'], count: number = 1): Promise<UploadResult[]> {
  return new Promise((resolve, reject) => {
    uni.chooseImage({
      count,
      sizeType: ['compressed'],
      sourceType,
      success(res) {
        uploadMultipleFiles(res.tempFilePaths).then(resolve).catch(reject)
      },
      fail(err) {
        reject(err)
      }
    })
  })
}
