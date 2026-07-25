<template>
  <div class="knowledge-base-page">
    <div class="page-header">
      <h2>知识库管理</h2>
      <p class="subtitle">上传和管理您的知识库文档，支持多种文件格式</p>
    </div>

    <div class="upload-section">
      <el-card class="upload-card">
        <template #header>
          <div class="card-header">
            <Upload class="header-icon" />
            <span>上传文档</span>
          </div>
        </template>
        <div class="upload-content">
          <el-upload
            ref="uploadRef"
            class="upload-area"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            multiple
            :limit="10"
            accept=".txt,.md,.json,.csv,.pdf,.docx,.html,.xml"
          >
            <div class="upload-icon-wrapper">
              <UploadFilled class="upload-icon" />
            </div>
            <div class="upload-text">
              <p class="main-text">将文件拖到此处，或<em>点击上传</em></p>
              <p class="sub-text">
                支持 TXT、MD、PDF、DOCX、JSON、CSV、HTML、XML 等格式（最多10个）
              </p>
            </div>
          </el-upload>

          <div class="upload-actions">
            <el-select
              v-model="selectedCategory"
              placeholder="选择分类"
              style="width: 160px"
            >
              <el-option label="通用知识" value="general" />
              <el-option label="产品文档" value="product" />
              <el-option label="政策法规" value="policy" />
              <el-option label="操作手册" value="manual" />
              <el-option label="FAQ" value="faq" />
            </el-select>

            <el-button
              type="primary"
              :disabled="fileList.length === 0 || uploading"
              @click="handleUpload"
              :loading="uploading"
            >
              {{ uploading ? "上传中..." : `上传 ${fileList.length} 个文件` }}
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <div class="documents-section">
      <el-card class="documents-card">
        <template #header>
          <div class="card-header">
            <Document class="header-icon" />
            <span>知识库文档</span>
            <el-tag size="small" type="info" class="count-tag"
              >共 {{ totalCount }} 个文档</el-tag
            >
          </div>
        </template>

        <div class="filter-bar">
          <el-select
            v-model="filterCategory"
            placeholder="全部分类"
            clearable
            style="width: 140px"
            @change="loadDocuments"
          >
            <el-option label="通用知识" value="general" />
            <el-option label="产品文档" value="product" />
            <el-option label="政策法规" value="policy" />
            <el-option label="操作手册" value="manual" />
            <el-option label="FAQ" value="faq" />
          </el-select>

          <el-button @click="loadDocuments" :icon="Refresh">刷新</el-button>
        </div>

        <el-table
          :data="documents"
          v-loading="loading"
          stripe
          class="documents-table"
        >
          <el-table-column prop="file_name" label="文件名" min-width="200">
            <template #default="{ row }">
              <div class="file-name-cell">
                <Document class="file-icon" />
                <span>{{ row.file_name }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="category" label="分类" width="120">
            <template #default="{ row }">
              <el-tag :type="getCategoryTagType(row.category)" size="small">
                {{ getCategoryLabel(row.category) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column
            prop="chunks_count"
            label="分块数"
            width="100"
            align="center"
          >
            <template #default="{ row }">
              <span class="chunks-count">{{ row.chunks_count }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                type="danger"
                size="small"
                text
                @click="handleDelete(row)"
              >
                <Delete /> 删除
              </el-button>
            </template>
          </el-table-column>

          <template #empty>
            <el-empty description="暂无知识库文档，请先上传文档" />
          </template>
        </el-table>

        <div class="pagination-wrapper" v-if="totalCount > pageSize">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="totalCount"
            layout="prev, pager, next"
            @current-change="loadDocuments"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Upload,
  UploadFilled,
  Document,
  Delete,
  Refresh,
} from "@element-plus/icons-vue";
import { knowledgeApi } from "@/api";

interface FileItem {
  name: string;
  raw: File;
  size: number;
}

interface DocumentItem {
  file_id: string;
  file_name: string;
  category: string;
  chunks_count: number;
}

const uploadRef = ref();
const fileList = ref<FileItem[]>([]);
const selectedCategory = ref("general");
const uploading = ref(false);
const documents = ref<DocumentItem[]>([]);
const totalCount = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);
const loading = ref(false);
const filterCategory = ref("");

const handleFileChange = (uploadFile: any, uploadFiles: any[]) => {
  if (
    uploadFile.raw &&
    !fileList.value.find((f) => f.name === uploadFile.name)
  ) {
    fileList.value.push({
      name: uploadFile.name,
      raw: uploadFile.raw,
      size: uploadFile.size,
    });
  }
  if (uploadFile.status === "removed") {
    fileList.value = fileList.value.filter((f) => f.name !== uploadFile.name);
  }
};

const handleExceed = () => {
  ElMessage.warning("最多只能上传 10 个文件");
};

const handleUpload = async () => {
  if (fileList.value.length === 0) return;

  uploading.value = true;
  try {
    const files = fileList.value.map((f) => f.raw);

    if (files.length === 1) {
      await knowledgeApi.uploadFile(files[0], selectedCategory.value);
    } else {
      await knowledgeApi.uploadBatch(files, selectedCategory.value);
    }

    ElMessage.success(`成功上传 ${files.length} 个文件`);
    fileList.value = [];
    if (uploadRef.value) {
      uploadRef.value.clearFiles();
    }
    loadDocuments();
  } catch (error: any) {
    ElMessage.error(error.message || "上传失败");
  } finally {
    uploading.value = false;
  }
};

const loadDocuments = async () => {
  loading.value = true;
  try {
    const params: { page: number; page_size: number; category?: string } = {
      page: currentPage.value,
      page_size: pageSize.value,
    };
    if (filterCategory.value) {
      params.category = filterCategory.value;
    }

    const result = await knowledgeApi.listDocuments(params);
    documents.value = result.list || [];
    totalCount.value = result.total || 0;
  } catch (error: any) {
    ElMessage.error(error.message || "加载文档列表失败");
  } finally {
    loading.value = false;
  }
};

const handleDelete = async (doc: DocumentItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${doc.file_name}" 吗？此操作不可恢复。`,
      "删除确认",
      {
        confirmButtonText: "确定删除",
        cancelButtonText: "取消",
        type: "warning",
      },
    );

    await knowledgeApi.deleteDocument(doc.file_id);
    ElMessage.success("删除成功");
    loadDocuments();
  } catch (e: any) {
    if (e !== "cancel") {
      ElMessage.error(e.message || "删除失败");
    }
  }
};

const getCategoryLabel = (category: string): string => {
  const labels: Record<string, string> = {
    general: "通用知识",
    product: "产品文档",
    policy: "政策法规",
    manual: "操作手册",
    faq: "FAQ",
  };
  return labels[category] || "未知分类";
};

const getCategoryTagType = (category: string): string => {
  const types: Record<string, string> = {
    general: "info",
    product: "success",
    policy: "warning",
    manual: "primary",
    faq: "",
  };
  return types[category] || "info";
};

onMounted(() => {
  loadDocuments();
});
</script>

<style scoped>
.knowledge-base-page {
  padding: 24px;
  max-width: 1200px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a18;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.upload-section {
  margin-bottom: 24px;
}

.upload-card {
  border-radius: 12px;
  border: 1px solid #e5e5e5;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.header-icon {
  color: #ff5600;
  font-size: 20px;
}

.upload-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-area :deep(.el-upload-dragger) {
  border-radius: 12px;
  border: 2px dashed #d9d9d9;
  padding: 32px;
  transition: all 0.3s;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: #ff5600;
}

.upload-area :deep(.el-upload-dragger.is-dragover) {
  border-color: #ff5600;
  background: rgba(255, 86, 0, 0.04);
}

.upload-icon-wrapper {
  margin-bottom: 12px;
}

.upload-icon {
  font-size: 48px;
  color: #ff5600;
}

.upload-text {
  text-align: center;
}

.main-text {
  font-size: 16px;
  color: #333;
  margin: 0 0 8px 0;
}

.main-text em {
  color: #ff5600;
  font-style: normal;
}

.sub-text {
  font-size: 13px;
  color: #999;
  margin: 0;
}

.upload-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.documents-card {
  border-radius: 12px;
  border: 1px solid #e5e5e5;
}

.count-tag {
  margin-left: 12px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.documents-table {
  border-radius: 8px;
  overflow: hidden;
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: #999;
  font-size: 16px;
}

.chunks-count {
  font-weight: 500;
  color: #333;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

@media (max-width: 768px) {
  .knowledge-base-page {
    padding: 16px;
  }

  .upload-actions {
    flex-direction: column;
  }

  .upload-actions .el-button {
    width: 100%;
  }

  .upload-actions .el-select {
    width: 100% !important;
  }
}
</style>
