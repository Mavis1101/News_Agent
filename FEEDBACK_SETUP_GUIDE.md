# Feedback Setup Guide

## 总览

目标：实现无跳转的邮件反馈体验

### 按钮设计

-   👍 Useful → Apps Script
-   👎 Not relevant → Apps Script
-   ⚑ Report issue → Google Form
-   Unsubscribe → Google Form

------------------------------------------------------------------------

## 需要创建的资源

1.  Google Sheet（存数据）
2.  Apps Script Web App
3.  Issue Form
4.  Unsubscribe Form

------------------------------------------------------------------------

## Part 1：Google Sheet

创建表头：

    Timestamp | Date | Rating | Source

------------------------------------------------------------------------

## Part 2：Apps Script

### 核心代码

``` javascript
const SHEET_ID = 'YOUR_SHEET_ID';

function doGet(e) {
  const rating = e.parameter.rating;
  const date = e.parameter.date;

  const sheet = SpreadsheetApp.openById(SHEET_ID).getActiveSheet();
  sheet.appendRow([
    new Date(),
    date,
    rating,
    'email'
  ]);

  return HtmlService.createHtmlOutput("Thanks!");
}
```

### 部署

-   Deploy → Web App
-   Access：Anyone

------------------------------------------------------------------------

## Part 3：Issue Form

字段： - Issue type - Description - Email（optional）

------------------------------------------------------------------------

## Part 4：Unsubscribe Form

字段： - Email（必填） - Reason（可选）

------------------------------------------------------------------------

## Part 5：更新 HTML

``` javascript
const GAS_WEB_APP_URL = '...';
const FORM_ISSUE_URL = '...';
const FORM_UNSUB_URL = '...';
```

------------------------------------------------------------------------

## 验收 Checklist

-   Sheet 正常写入
-   Web App 可访问
-   表单正常
-   Email 按钮正常

------------------------------------------------------------------------

## 日常使用

-   查看反馈：Google Sheet
-   处理退订：删除 subscribers.json
-   查看 issue：Sheet

------------------------------------------------------------------------

## 核心指标

-   点击率
-   退订率
-   反馈量
