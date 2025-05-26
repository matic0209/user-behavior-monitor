class MouseEventTracker {
    constructor() {
        this.events = [];
        this.isTracking = false;
        this.startTime = null;
    }

    startTracking() {
        if (this.isTracking) return;
        
        this.isTracking = true;
        this.startTime = Date.now();
        this.events = [];
        
        // 添加所有鼠标事件监听器
        document.addEventListener('mousemove', this.handleMouseEvent.bind(this));
        document.addEventListener('mousedown', this.handleMouseEvent.bind(this));
        document.addEventListener('mouseup', this.handleMouseEvent.bind(this));
        document.addEventListener('click', this.handleMouseEvent.bind(this));
        document.addEventListener('dblclick', this.handleMouseEvent.bind(this));
        document.addEventListener('contextmenu', this.handleMouseEvent.bind(this));
    }

    stopTracking() {
        if (!this.isTracking) return;
        
        this.isTracking = false;
        
        // 移除所有鼠标事件监听器
        document.removeEventListener('mousemove', this.handleMouseEvent.bind(this));
        document.removeEventListener('mousedown', this.handleMouseEvent.bind(this));
        document.removeEventListener('mouseup', this.handleMouseEvent.bind(this));
        document.removeEventListener('click', this.handleMouseEvent.bind(this));
        document.removeEventListener('dblclick', this.handleMouseEvent.bind(this));
        document.removeEventListener('contextmenu', this.handleMouseEvent.bind(this));
    }

    handleMouseEvent(event) {
        const eventData = {
            type: event.type,
            timestamp: Date.now() - this.startTime,
            x: event.clientX,
            y: event.clientY,
            target: {
                tagName: event.target.tagName,
                id: event.target.id,
                className: event.target.className
            },
            button: event.button,
            buttons: event.buttons
        };

        this.events.push(eventData);
    }

    getEventStream() {
        return this.events;
    }

    clearEvents() {
        this.events = [];
    }
}

// 使用示例
const tracker = new MouseEventTracker();

// 开始追踪
tracker.startTracking();

// 停止追踪
// tracker.stopTracking();

// 获取事件流
// const eventStream = tracker.getEventStream();
// console.log(eventStream); 