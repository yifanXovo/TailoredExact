#pragma once

#include <vector>
#include <numeric>
#include <cmath>
#include <algorithm>
#include <stdexcept>
#include <iostream>

class AVLCalculator {
public:
    explicit AVLCalculator(const std::vector<double>& initial_a)
        : root(nullptr), total_target_value(0.0), current_a(initial_a) {
        if (initial_a.empty()) {
            return;
        }
        for (double val : initial_a) {
            add_element(val);
        }
    }

    ~AVLCalculator() {
        destroy_tree(root);
    }

    AVLCalculator(const AVLCalculator&) = delete;
    AVLCalculator& operator=(const AVLCalculator&) = delete;

    double sumAbsToAll(double val) {
        return calculate_contribution(val);
    }

    void update(int x_idx, int y_idx, double new_x_val, double new_y_val) {
        if (x_idx < 0 || x_idx >= current_a.size() || y_idx < 0 || y_idx >= current_a.size()) {
            std::cout << x_idx << " " << y_idx << " " << new_x_val << " " << new_y_val << std::endl;
            throw std::out_of_range("Index out of range.");
        }

        double old_x_val = current_a[x_idx];
        double old_y_val = current_a[y_idx];

        if (x_idx == y_idx) {
            remove_element(old_x_val);
            add_element(new_x_val);
            current_a[x_idx] = new_x_val;
        }
        else {
            remove_element(old_x_val);
            remove_element(old_y_val);

            add_element(new_x_val);
            add_element(new_y_val);

            current_a[x_idx] = new_x_val;
            current_a[y_idx] = new_y_val;
        }
    }

    double getTargetValue() const {
        return total_target_value;
    }

    double getTotalSum() const {
        return sum(root);
    }

    int getTotalCount() const {
        return size(root);
    }

    double getGiniCoefficient() const {
        double denom = static_cast<double>(size(root)) * sum(root);
        if (denom <= 1e-12) return 0.0;
        return total_target_value / denom;
    }

private:
    struct Node {
        double key;
        int count; // Duplicate values
        int height;
        int subtree_size;
        double subtree_sum;
        Node* left;
        Node* right;

        Node(double k) : key(k), count(1), height(1), subtree_size(1), subtree_sum(k), left(nullptr), right(nullptr) {}
    };

    Node* root;
    double total_target_value;
    std::vector<double> current_a;

    int height(Node* n) { return n ? n->height : 0; }
    int size(Node* n) { return n ? n->subtree_size : 0; }
    double sum(Node* n) { return n ? n->subtree_sum : 0.0; }
    int size(const Node* n) const { return n ? n->subtree_size : 0; }
    double sum(const Node* n) const { return n ? n->subtree_sum : 0.0; }

    void update_node_metrics(Node* n) {
        if (n) {
            n->height = 1 + std::max(height(n->left), height(n->right));
            n->subtree_size = size(n->left) + size(n->right) + n->count;
            n->subtree_sum = sum(n->left) + sum(n->right) + (double)n->count * n->key;
        }
    }

    Node* right_rotate(Node* y) {
        Node* x = y->left;
        Node* T2 = x->right;
        x->right = y;
        y->left = T2;
        update_node_metrics(y);
        update_node_metrics(x);
        return x;
    }

    Node* left_rotate(Node* x) {
        Node* y = x->right;
        Node* T2 = y->left;
        y->left = x;
        x->right = T2;
        update_node_metrics(x);
        update_node_metrics(y);
        return y;
    }

    int get_balance(Node* n) {
        return n ? height(n->left) - height(n->right) : 0;
    }

    Node* insert(Node* node, double key) {
        if (!node) return new Node(key);

        if (key < node->key) {
            node->left = insert(node->left, key);
        }
        else if (key > node->key) {
            node->right = insert(node->right, key);
        }
        else {
            node->count++;
            update_node_metrics(node);
            return node;
        }

        update_node_metrics(node);

        int balance = get_balance(node);

        if (balance > 1 && key < node->left->key)
            return right_rotate(node);
        if (balance < -1 && key > node->right->key)
            return left_rotate(node);
        if (balance > 1 && key > node->left->key) {
            node->left = left_rotate(node->left);
            return right_rotate(node);
        }
        if (balance < -1 && key < node->right->key) {
            node->right = right_rotate(node->right);
            return left_rotate(node);
        }

        return node;
    }

    Node* min_value_node(Node* node) {
        Node* current = node;
        while (current->left != nullptr)
            current = current->left;
        return current;
    }

    Node* remove(Node* node, double key) {
        if (!node) return node;

        if (key < node->key) {
            node->left = remove(node->left, key);
        }
        else if (key > node->key) {
            node->right = remove(node->right, key);
        }
        else {
            if (node->count > 1) {
                node->count--;
                update_node_metrics(node);
                return node;
            }
            if (!node->left || !node->right) {
                Node* temp = node->left ? node->left : node->right;
                delete node;
                return temp;
            }
            Node* temp = min_value_node(node->right);
            node->key = temp->key;
            node->count = 1;
            node->right = remove(node->right, temp->key);
        }

        if (!node) return node;

        update_node_metrics(node);

        int balance = get_balance(node);

        if (balance > 1 && get_balance(node->left) >= 0)
            return right_rotate(node);
        if (balance > 1 && get_balance(node->left) < 0) {
            node->left = left_rotate(node->left);
            return right_rotate(node);
        }
        if (balance < -1 && get_balance(node->right) <= 0)
            return left_rotate(node);
        if (balance < -1 && get_balance(node->right) > 0) {
            node->right = right_rotate(node->right);
            return left_rotate(node);
        }

        return node;
    }

    void destroy_tree(Node* node) {
        if (node) {
            destroy_tree(node->left);
            destroy_tree(node->right);
            delete node;
        }
    }

    std::pair<int, double> query_less(Node* node, double key) {
        int cnt = 0; double sm = 0;
        while (node) {
            if (key <= node->key) node = node->left;
            else { cnt += size(node->left) + node->count;
                sm  += sum(node->left)  + (double)node->count * node->key;
                node = node->right; }
        }
        return {cnt, sm};
    }

    double calculate_contribution(double val) {
        auto less_stats = query_less(root, val);
        int count_less = less_stats.first;
        double sum_less = less_stats.second;

        int total_count = size(root);
        double total_sum_val = sum(root);

        int count_greater_equal = total_count - count_less;
        double sum_greater_equal = total_sum_val - sum_less;

        double contribution = (double)val * count_less - sum_less;
        contribution += sum_greater_equal - (double)val * count_greater_equal;

        return contribution;
    }

    void add_element(double val) {
        double contribution = calculate_contribution(val);
        total_target_value += contribution;
        root = insert(root, val);
    }

    void remove_element(double val) {
        double contribution = calculate_contribution(val);
        total_target_value -= contribution;
        root = remove(root, val);
    }
};
