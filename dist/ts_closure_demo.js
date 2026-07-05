"use strict";
// ============================================
// TypeScript 闭包 (Closure) 演示
// 目标：直观展示词法作用域、函数作为返回值
//       及内部变量引用等核心概念
// ============================================
// ============================================
// 1. 基础闭包：函数作为返回值
// ============================================
console.log("========== 1. 基础闭包：函数作为返回值 ==========");
function outerFunction() {
    const secretMessage = "Hello, Closure!"; // 外部函数的局部变量
    // 内部函数可以访问外部函数的变量
    return function innerFunction() {
        return secretMessage;
    };
}
const closure = outerFunction();
console.log("通过闭包获取的变量值:", closure());
// ✅ 即使 outerFunction 已执行完毕，innerFunction 仍能访问 secretMessage
console.log("\n========== 2. 词法作用域演示 ==========");
// 词法作用域：函数在定义时确定其作用域链，而非调用时
const globalVar = "global";
function createScopeDemo() {
    const localVar = "local";
    return function displayScope() {
        console.log("全局变量:", typeof globalVar !== 'undefined' ? globalVar : "未定义"); // ✅ 可访问
        console.log("局部变量:", localVar); // ✅ 可访问
    };
}
const scopeDemo = createScopeDemo();
console.log("调用闭包函数查看作用域：");
scopeDemo();
console.log("\n========== 3. 数据封装与私有变量 ==========");
// 使用闭包实现类似私有变量的效果
function createCounter(initialValue) {
    let count = initialValue; // "私有"变量，外部无法直接访问
    return {
        increment: function () {
            count++;
            console.log(`increment: count = ${count}`);
            return count;
        },
        decrement: function () {
            count--;
            console.log(`decrement: count = ${count}`);
            return count;
        },
        getCount: function () {
            console.log(`getCount: count = ${count}`);
            return count;
        }
    };
}
const counter1 = createCounter(0);
counter1.increment(); // count = 1
counter1.increment(); // count = 2
counter1.decrement(); // count = 1
// console.log(counter1.count); // ❌ undefined - 无法直接访问内部变量
console.log("\n========== 4. 多个闭包共享同一作用域 ==========");
function createSharedEnvironment() {
    let sharedValue = "shared";
    function updater(newValue) {
        sharedValue = newValue;
        console.log(`[Updater] 更新后的值: ${sharedValue}`);
    }
    return function reader() {
        console.log(`[Reader] 读取到的值: ${sharedValue}`);
        // 可以通过闭包修改共享变量（通过 updater）
        updater(sharedValue + "_modified");
    };
}
const env = createSharedEnvironment();
env(); // Reader读取 -> Updater修改
console.log("\n========== 5. 实用场景：函数工厂 ==========");
// 创建带特定参数的乘法器 - 使用泛型约束演示更复杂的示例
function createMultiplierFactory(factor) {
    return function multiplier(number) {
        return number * factor;
    };
}
const double = createMultiplierFactory(2);
const triple = createMultiplierFactory(3);
console.log("double(5):", double(5)); // 10
console.log("triple(5):", triple(5)); // 15
console.log("\n========== 6. 实用场景：防抖函数 ==========");
function debounce(func, delay) {
    let timerId = null; // 闭包保存定时器ID
    return function (...args) {
        if (timerId) {
            clearTimeout(timerId);
        }
        timerId = setTimeout(() => {
            func.apply(undefined, args);
            timerId = null;
        }, delay);
    };
}
const logDebounced = debounce((msg) => console.log("防抖输出:", msg), 1000);
console.log("防抖函数已创建（触发需要等待1秒）");
console.log("\n========== 7. 闭包的注意事项 ==========");
// 注意：循环中的闭包常见陷阱
console.log("传统 for 循环的问题:");
for (let i = 1; i <= 3; i++) { // 使用 let 确保块级作用域（TS推荐做法）
    setTimeout(() => {
        console.log(`i = ${i}`); // 输出: 1, 2, 3（✅ TypeScript 中推荐使用 let）
    }, 100);
}
console.log("使用 const 的解决方案:");
for (let j = 1; j <= 3; j++) { // ✅ let 有块级作用域
    setTimeout(() => {
        console.log(`j = ${j}`); // 输出: 1, 2, 3
    }, 200);
}
console.log("\n========== 演示结束 ==========");
