import matplotlib.pyplot as plt


def plot_step_switch(switch_index: int, total_length: int, title: str):
    y = [1 if i < switch_index else 0 for i in range(total_length)]
    x = list(range(total_length))
    fig, ax = plt.subplots(figsize=(9,5))
    ax.plot(x, y, marker='o')

    ax.set_ylim(-0.05, 1.05)
    ax.set_xlim(-0.5, total_length - 0.5)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['0', '1'], color='gray', fontweight='bold', fontsize=12)

    ax.set_xticks(x)
    ax.set_xticklabels([str(i) for i in x], color='gray', fontweight='bold', fontsize=12)
    ax.tick_params(axis='x', length=0)

    ax.set_xlabel('Distance (Ft)', color='black', fontweight='bold', fontsize=14)
    ax.set_ylabel('Presence', color='black', fontweight='bold', fontsize=14)

    ax.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(True)

    ax.hlines(y=1, xmin=-0.5, xmax=total_length - 0.5, colors='gray', linestyles='dashed', linewidth=1)
    ax.hlines(y=0, xmin=-0.5, xmax=total_length - 0.5, colors='gray', linestyles='dashed', linewidth=1)

    plt.title(title, color='black', fontweight='bold')
    plt.show()


def main():
    plot_step_switch(20, total_length=22, title='Lateral Distance')
    plot_step_switch(15, total_length=22, title='Longitudal Distance')


if __name__ == "__main__":
    main()
