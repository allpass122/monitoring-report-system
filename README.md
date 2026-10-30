# 營造監測工程報表管理系統 — 專案介紹頁

履歷用的單頁靜態網頁，介紹一套營造監測顧問公司的內部系統（獨立全端開發）。純 HTML + CSS，無框架、無 build step，直接部署到 GitHub Pages。

## 結構

```
index.html            單頁內容
style.css             樣式
assets/               處理後的截圖（WebP，已遮罩敏感資訊）
tools/
  process-images.py   從素材包原檔產生 assets/（裁切、實色矩形遮罩、縮放、轉 WebP）
  redactions.json     每張圖的裁切範圍與遮罩座標（原圖像素）
```

## 重跑圖片處理

素材包不在此 repo（含未遮罩原檔，不公開）。

```sh
python3 -m venv .venv && .venv/bin/pip install Pillow
.venv/bin/python -I tools/process-images.py <素材包路徑> assets
```

## 部署

GitHub repo → Settings → Pages → Source: Deploy from a branch → `main` / `(root)`。
