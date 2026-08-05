<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <!-- Logo 区域 -->
      <div class="logo-area" @click="isCollapse = !isCollapse">
        <span class="logo-icon">🌸</span>
        <span v-show="!isCollapse" class="logo-text">HX Mall</span>
      </div>

      <!-- 菜单 -->
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/products">
          <el-icon><Goods /></el-icon>
          <template #title>商品管理</template>
        </el-menu-item>
        <el-menu-item index="/cases">
          <el-icon><PictureFilled /></el-icon>
          <template #title>案例管理</template>
        </el-menu-item>
        <el-menu-item index="/orders">
          <el-icon><Document /></el-icon>
          <template #title>订单管理</template>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧主体 -->
    <el-container>
      <!-- 顶部栏 -->
      <el-header class="top-header">
        <div class="header-left">
          <el-button
            class="collapse-btn"
            :icon="isCollapse ? Expand : Fold"
            text
            @click="isCollapse = !isCollapse"
          />
          <span class="header-title">HX Mall 管理后台</span>
        </div>

        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-info">
              <el-icon><UserFilled /></el-icon>
              <span class="user-phone">{{ userStore.userInfo?.phone || '管理员' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  DataAnalysis,
  Goods,
  PictureFilled,
  Document,
  User,
  Fold,
  Expand,
  UserFilled,
  ArrowDown,
  SwitchButton,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)

// 根据当前路由匹配活动菜单项
const activeMenu = computed(() => {
  const path = route.path
  // 匹配第一级子路由，如 /products/create -> /products
  const segments = path.split('/').filter(Boolean)
  if (segments.length === 0) return '/dashboard'
  return '/' + segments[0]
})

async function handleCommand(command: string) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
      userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch {
      // 用户取消
    }
  }
}
</script>

<style scoped lang="scss">
.main-layout {
  height: 100vh;
}

// ===== 侧边栏 =====
.sidebar {
  background: #fff;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.04);
  transition: width 0.3s;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.logo-area {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 60px;
  padding: 0 16px;
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid var(--color-border);
}

.logo-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.logo-text {
  margin-left: 10px;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
  white-space: nowrap;
  overflow: hidden;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  overflow-y: auto;

  .el-menu-item {
    font-size: 15px;

    &.is-active {
      color: var(--color-primary);
      background: var(--color-primary-light);
      border-right: 3px solid var(--color-primary);
    }
  }

  // 折叠状态下也保持激活样式
  &.el-menu--collapse {
    .el-menu-item.is-active {
      border-right: 3px solid var(--color-primary);
    }
  }
}

// ===== 顶部栏 =====
.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapse-btn {
  font-size: 20px;
  padding: 4px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  transition: background 0.2s;

  &:hover {
    background: var(--color-primary-light);
  }

  .user-phone {
    font-size: 14px;
    color: var(--color-text);
  }

  .el-icon {
    color: var(--color-text-secondary);
  }
}

// ===== 内容区 =====
.main-content {
  background: var(--color-bg);
  padding: 24px;
  overflow-y: auto;
}
</style>
