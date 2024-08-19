import matplotlib.pyplot as plt

def plot_simple_graph():
    # 创建数据
    x = [1, 2, 3, 4, 5]
    y = [1, 4, 9, 16, 25]

    # 创建图表
    plt.figure(figsize=(8, 6))
    plt.plot(x, y, marker='o', linestyle='-', color='b')

    # 设置图表标题和标签
    plt.title('Simple Line Graph')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')

    # 显示图表
    plt.show()

if __name__ == "__main__":
    plot_simple_graph()
