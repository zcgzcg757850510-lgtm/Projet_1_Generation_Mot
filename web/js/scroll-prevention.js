/**
 * 全局禁止向下滑动模块
 * 防止页面下拉刷新和过度滚动
 */

class ScrollPrevention {
    constructor() {
        this.init();
    }

    init() {
        this.preventTouchScroll();
        this.preventWheelScroll();
        this.preventKeyboardScroll();
        console.log('🚫 全局下拉滑动禁止已启用');
    }

    /**
     * 防止触摸滑动
     */
    preventTouchScroll() {
        let startY = 0;
        let startX = 0;

        // 记录触摸开始位置
        document.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
            startX = e.touches[0].clientX;
        }, { passive: false });

        // 防止下拉刷新和过度滚动
        document.addEventListener('touchmove', (e) => {
            // 检查是否在允许滚动的区域内
            const allowScrollSelectors = [
                '#currentParamsPreview',  // 参数预览区域
                '#presetList',            // 预设列表区域
                '.preset-item-card',      // 预设卡片
                '#articleModal .viewport', // 文章生成模态框的内容区域
                '#articleModal',          // 整个文章生成模态框
                '[style*="overflow-y: auto"]', // 显式设置了overflow-y: auto的元素
                '[style*="overflow: auto"]',   // 显式设置了overflow: auto的元素
                '.scrollable'             // 标记为可滚动的元素
            ];
            
            const isInScrollableArea = allowScrollSelectors.some(selector => 
                e.target.closest(selector)
            );
            
            if (isInScrollableArea) {
                // 允许在指定区域内滚动
                return true;
            }

            // 检查是否在弹窗内部但不在允许滚动的区域
            const isInModal = e.target.closest('.modal:not(.hidden)');
            if (isInModal) {
                // 禁用弹窗内其他区域的滚动
                e.preventDefault();
                return false;
            }

            // 禁用主界面的滚动（防止下拉刷新）
            const currentY = e.touches[0].clientY;
            const deltaY = currentY - startY;
            
            // 只阻止向下滚动到页面顶部时的下拉动作
            if (window.scrollY === 0 && deltaY > 0) {
                e.preventDefault();
                return false;
            }
        }, { passive: false });

        // 防止触摸结束时的惯性滚动
        document.addEventListener('touchend', (e) => {
            // 阻止默认的触摸结束行为
            if (window.scrollY === 0) {
                e.preventDefault();
            }
        }, { passive: false });
    }

    /**
     * 防止鼠标滚轮过度滚动
     */
    preventWheelScroll() {
        document.addEventListener('wheel', (e) => {
            // 检查是否在允许滚动的区域内
            const allowScrollSelectors = [
                '#currentParamsPreview',  // 参数预览区域
                '#presetList',            // 预设列表区域
                '.preset-item-card',      // 预设卡片
                '#articleModal .viewport', // 文章生成模态框的内容区域
                '#articleModal',          // 整个文章生成模态框
                '[style*="overflow-y: auto"]', // 显式设置了overflow-y: auto的元素
                '[style*="overflow: auto"]',   // 显式设置了overflow: auto的元素
                '.scrollable'             // 标记为可滚动的元素
            ];
            
            const isInScrollableArea = allowScrollSelectors.some(selector => 
                e.target.closest(selector)
            );
            
            if (isInScrollableArea) {
                // 允许在指定区域内滚动
                return true;
            }

            // 检查是否在弹窗内部但不在允许滚动的区域
            const isInModal = e.target.closest('.modal:not(.hidden)');
            if (isInModal) {
                // 禁用弹窗内其他区域的滚动
                e.preventDefault();
                return false;
            }

            // 禁用主界面的滚动（防止页面过度滚动）
            e.preventDefault();
            return false;
        }, { passive: false });
    }

    /**
     * 防止键盘滚动到边界外
     */
    preventKeyboardScroll() {
        document.addEventListener('keydown', (e) => {
            // 检查是否在允许滚动的区域内
            const allowScrollSelectors = [
                '#currentParamsPreview',  // 参数预览区域
                '#presetList',            // 预设列表区域
                '.preset-item-card',      // 预设卡片
                '#articleModal .viewport', // 文章生成模态框的内容区域
                '#articleModal',          // 整个文章生成模态框
                '[style*="overflow-y: auto"]', // 显式设置了overflow-y: auto的元素
                '[style*="overflow: auto"]',   // 显式设置了overflow: auto的元素
                '.scrollable'             // 标记为可滚动的元素
            ];
            
            const isInScrollableArea = allowScrollSelectors.some(selector => 
                e.target.closest(selector)
            );
            
            if (isInScrollableArea) {
                // 允许在指定区域内使用键盘滚动
                return true;
            }

            // 检查是否在弹窗内部但不在允许滚动的区域
            const isInModal = e.target.closest('.modal:not(.hidden)');
            if (isInModal) {
                // 禁用弹窗内其他区域的键盘滚动
                const preventKeys = [32, 33, 34, 35, 36, 38, 40]; // Space, PageUp, PageDown, End, Home, ArrowUp, ArrowDown
                if (preventKeys.includes(e.keyCode)) {
                    e.preventDefault();
                    return false;
                }
            }

            // 禁用主界面的键盘滚动
            const preventKeys = [32, 33, 34, 35, 36, 38, 40]; // Space, PageUp, PageDown, End, Home, ArrowUp, ArrowDown
            if (preventKeys.includes(e.keyCode)) {
                e.preventDefault();
                return false;
            }
        });
    }

    /**
     * 禁用浏览器默认的下拉刷新
     */
    static disablePullToRefresh() {
        // 添加CSS样式禁用下拉刷新
        const style = document.createElement('style');
        style.textContent = `
            html, body {
                overscroll-behavior-y: none !important;
                -webkit-overscroll-behavior-y: none !important;
                -ms-overscroll-behavior-y: none !important;
            }
            
            /* 禁用iOS Safari的弹性滚动 */
            body {
                -webkit-overflow-scrolling: auto !important;
                overflow-scrolling: auto !important;
            }
            
            /* 禁用Chrome的下拉刷新 */
            body {
                overscroll-behavior: none !important;
                -webkit-overscroll-behavior: none !important;
            }
        `;
        document.head.appendChild(style);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 禁用浏览器默认的下拉刷新
    ScrollPrevention.disablePullToRefresh();
    
    // 初始化滚动防护
    window.scrollPrevention = new ScrollPrevention();
});

// 导出到全局
window.ScrollPrevention = ScrollPrevention;
